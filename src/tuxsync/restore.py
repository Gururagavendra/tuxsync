"""
Restore module for TuxSync.
Handles restoring packages and configurations using tuxmate-cli as executor.
"""

import logging
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_config
from .storage import get_storage_backend

console = Console()
logger = logging.getLogger(__name__)


class TuxMateExecutor:
    """
    Executor that uses TuxMate CLI for package installation.

    Follows loose coupling principle - TuxSync is the brain,
    TuxMate CLI is the hands.
    """

    def __init__(self):
        self._tuxmate_cli_path: Optional[str] = None
        self._config = get_config()

    def find_tuxmate_cli(self) -> Optional[str]:
        """
        Find tuxmate-cli in PATH.

        Returns:
            Path to tuxmate-cli if found, None otherwise.
        """
        return shutil.which("tuxmate-cli")

    def download_tuxmate_cli(self) -> str:
        """
        Download tuxmate-cli.sh to /tmp for temporary use.

        Returns:
            Path to downloaded tuxmate-cli.sh.

        Raises:
            RuntimeError: If download fails.
        """
        console.print("[blue]TuxMate CLI not found in PATH. Downloading...[/blue]")
        logger.info("TuxMate CLI not found, attempting download")

        tmp_path = self._config.tmp_dir / "tuxmate-cli.sh"

        # Try multiple download sources from config
        download_urls = [
            self._config.tuxmate_cli_release_url,
            self._config.tuxmate_cli_fallback_url,
        ]

        for url in download_urls:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(f"Downloading from {url}...", total=None)

                    result = subprocess.run(
                        ["curl", "-fsSL", "-o", str(tmp_path), url],
                        capture_output=True,
                        text=True,
                        timeout=self._config.network_timeout,
                    )

                    progress.update(task, completed=True)

                if result.returncode == 0 and tmp_path.exists():
                    # Make executable
                    tmp_path.chmod(
                        tmp_path.stat().st_mode
                        | stat.S_IXUSR
                        | stat.S_IXGRP
                        | stat.S_IXOTH
                    )
                    console.print(
                        f"[green]✓ TuxMate CLI downloaded to {tmp_path}[/green]"
                    )
                    logger.info(f"TuxMate CLI downloaded to {tmp_path}")
                    return str(tmp_path)

            except subprocess.TimeoutExpired:
                logger.warning(f"Download timed out from {url}")
                continue
            except subprocess.SubprocessError as e:
                logger.warning(f"Download failed from {url}: {e}")
                continue

        # If curl fails, try with wget
        try:
            result = subprocess.run(
                [
                    "wget",
                    "-q",
                    "-O",
                    str(tmp_path),
                    self._config.tuxmate_cli_fallback_url,
                ],
                capture_output=True,
                timeout=self._config.network_timeout,
            )
            if result.returncode == 0 and tmp_path.exists():
                tmp_path.chmod(
                    tmp_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                )
                logger.info(f"TuxMate CLI downloaded via wget to {tmp_path}")
                return str(tmp_path)
        except subprocess.SubprocessError as e:
            logger.warning(f"wget download failed: {e}")

        raise RuntimeError(
            "Failed to download TuxMate CLI. Please install it manually:\n"
            f"  curl -fsSL {self._config.tuxmate_cli_fallback_url} "
            "-o /usr/local/bin/tuxmate-cli.sh\n"
            "  chmod +x /usr/local/bin/tuxmate-cli.sh"
        )

    def get_tuxmate_cli(self) -> str:
        """
        Get path to tuxmate-cli, downloading if necessary.

        Returns:
            Path to tuxmate-cli executable or script.
        """
        if self._tuxmate_cli_path:
            return self._tuxmate_cli_path

        # Check if already in PATH
        path = self.find_tuxmate_cli()
        if path:
            console.print(f"[green]✓ Found TuxMate CLI at {path}[/green]")
            self._tuxmate_cli_path = path
            return path

        # Check for tuxmate-cli.sh script
        script_path = shutil.which("tuxmate-cli.sh")
        if script_path:
            console.print(f"[green]✓ Found TuxMate CLI script at {script_path}[/green]")
            self._tuxmate_cli_path = script_path
            return script_path

        # Download to /tmp
        self._tuxmate_cli_path = self.download_tuxmate_cli()
        return self._tuxmate_cli_path

    def install_packages(self, packages: list[str], dry_run: bool = False) -> bool:
        """
        Install packages using tuxmate-cli.

        Args:
            packages: List of package names to install.
            dry_run: If True, only show what would be installed.

        Returns:
            True if installation succeeded.
        """
        if not packages:
            console.print("[yellow]No packages to install[/yellow]")
            return True

        tuxmate_cli = self.get_tuxmate_cli()

        console.print(
            f"\n[blue]Installing {len(packages)} packages via TuxMate CLI...[/blue]"
        )
        logger.info(f"Starting installation of {len(packages)} packages")

        if dry_run:
            console.print("[yellow]DRY RUN - Would install:[/yellow]")
            for pkg in packages:
                console.print(f"  • {pkg}")
            return True

        # Use tuxmate-cli install command
        try:
            # Install packages in batches to avoid command line length limits
            batch_size = self._config.package_batch_size
            all_success = True
            failed_batches = []

            for i in range(0, len(packages), batch_size):
                batch = packages[i : i + batch_size]
                batch_num = i // batch_size + 1
                console.print(
                    f"[dim]Installing batch {batch_num}: {len(batch)} packages[/dim]"
                )
                logger.debug(f"Installing batch {batch_num}: {batch}")

                cmd = [tuxmate_cli, "install"] + batch
                if tuxmate_cli.endswith(".sh"):
                    # If using the script, add --yes to skip prompts
                    cmd.append("--yes")

                result = subprocess.run(
                    cmd,
                    capture_output=False,  # Let output show to user
                    text=True,
                )

                if result.returncode != 0:
                    console.print(
                        f"[red]✗ Batch {batch_num} failed with "
                        f"exit code {result.returncode}[/red]"
                    )
                    logger.error(
                        f"Batch {batch_num} failed (exit {result.returncode}): {batch}"
                    )
                    all_success = False
                    failed_batches.append(batch_num)
                    # Continue with other batches instead of failing completely

            if all_success:
                console.print("[green]✓ All packages installed successfully[/green]")
                logger.info("All packages installed successfully")
            else:
                console.print(
                    f"[yellow]⚠ {len(failed_batches)} batch(es) failed[/yellow]"
                )
                logger.warning(f"Failed batches: {failed_batches}")

            return all_success

        except subprocess.SubprocessError as e:
            console.print(f"[red]Installation failed: {e}[/red]")
            logger.error(f"Installation subprocess error: {e}")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            logger.exception(f"Unexpected installation error: {e}")
            return False


class RestoreManager:
    """Manages the restore process."""

    def __init__(self):
        self.executor = TuxMateExecutor()

    def restore_bashrc(
        self,
        content: str,
        backup_existing: bool = True,
        merge: bool = False,
    ) -> bool:
        """
        Restore .bashrc content.

        Args:
            content: The bashrc content to restore.
            backup_existing: Whether to backup existing .bashrc.
            merge: Whether to merge with existing (append) instead of replace.

        Returns:
            True if restoration succeeded.
        """
        bashrc_path = Path.home() / ".bashrc"

        if bashrc_path.exists():
            if backup_existing:
                # Create backup with timestamp
                import datetime

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = bashrc_path.with_suffix(f".backup_{timestamp}")

                console.print(
                    f"[blue]Backing up existing .bashrc to {backup_path}[/blue]"
                )
                shutil.copy2(bashrc_path, backup_path)

            if merge:
                # Append to existing
                console.print("[blue]Merging .bashrc content...[/blue]")
                existing = bashrc_path.read_text()

                # Add separator and append
                separator = "\n\n# === TuxSync Restored Content ===\n"
                new_content = existing + separator + content
                bashrc_path.write_text(new_content)
            else:
                # Replace
                console.print("[blue]Replacing .bashrc...[/blue]")
                bashrc_path.write_text(content)
        else:
            bashrc_path.write_text(content)

        console.print("[green]✓ .bashrc restored[/green]")
        return True

    def restore(
        self,
        backup_id: str,
        storage_type: str = "github",
        server_url: Optional[str] = None,
        dry_run: bool = False,
        skip_packages: bool = False,
        skip_bashrc: bool = False,
        merge_bashrc: bool = False,
    ) -> bool:
        """
        Perform full restore from a backup.

        Args:
            backup_id: ID of the backup to restore.
            storage_type: "github" or "custom".
            server_url: URL for custom server.
            dry_run: Only show what would be done.
            skip_packages: Don't install packages.
            skip_bashrc: Don't restore bashrc.
            merge_bashrc: Merge instead of replace bashrc.

        Returns:
            True if restore succeeded.
        """
        console.print("\n[bold blue]═══ TuxSync Restore ═══[/bold blue]\n")

        try:
            # Get storage backend
            storage = get_storage_backend(storage_type, server_url)

            # Fetch backup
            console.print(f"[blue]Fetching backup: {backup_id}[/blue]")
            metadata, bashrc_content = storage.load(backup_id)

            # Show backup info
            console.print("\n[bold]Backup Information:[/bold]")
            console.print(f"  Created: {metadata.created_at}")
            console.print(f"  Source: {metadata.distro} {metadata.distro_version}")
            console.print(f"  Package Manager: {metadata.package_manager}")
            console.print(f"  Packages: {metadata.package_count}")
            console.print(f"  Has .bashrc: {metadata.has_bashrc}")
            console.print()

            success = True

            # Restore packages
            if not skip_packages and metadata.packages:
                console.print(
                    f"[bold]Restoring {len(metadata.packages)} packages...[/bold]"
                )
                if not self.executor.install_packages(metadata.packages, dry_run):
                    console.print(
                        "[yellow]⚠ Some packages may have failed to install[/yellow]"
                    )
                    success = False

            # Restore bashrc
            if not skip_bashrc and bashrc_content and metadata.has_bashrc:
                if dry_run:
                    console.print("[yellow]DRY RUN - Would restore .bashrc[/yellow]")
                else:
                    self.restore_bashrc(bashrc_content, merge=merge_bashrc)

            if success:
                console.print(
                    "\n[bold green]✓ Restore completed successfully![/bold green]"
                )
            else:
                console.print(
                    "\n[bold yellow]⚠ Restore completed with warnings[/bold yellow]"
                )

            return success

        except Exception as e:
            console.print(f"\n[bold red]✗ Restore failed: {e}[/bold red]")
            return False
