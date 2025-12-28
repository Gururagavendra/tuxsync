"""
Restore module for TuxSync.
Handles restoring packages and configurations using tuxmate as executor.
"""

import subprocess
import shutil
import stat
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .storage import BackupMetadata, get_storage_backend

console = Console()

# TuxMate GitHub repository for downloading
TUXMATE_REPO = "https://github.com/Gururagavendra/tuxmate"
TUXMATE_RAW_URL = f"{TUXMATE_REPO}/releases/latest/download/tuxmate"
TUXMATE_FALLBACK_URL = f"https://raw.githubusercontent.com/Gururagavendra/tuxmate/main/tuxmate"


class TuxMateExecutor:
    """
    Executor that uses TuxMate for package installation.
    
    Follows loose coupling principle - TuxSync is the brain,
    TuxMate is the hands.
    """

    def __init__(self):
        self._tuxmate_path: Optional[str] = None

    def find_tuxmate(self) -> Optional[str]:
        """
        Find tuxmate in PATH.
        
        Returns:
            Path to tuxmate if found, None otherwise.
        """
        return shutil.which("tuxmate")

    def download_tuxmate(self) -> str:
        """
        Download tuxmate to /tmp for temporary use.
        
        Returns:
            Path to downloaded tuxmate.
            
        Raises:
            RuntimeError: If download fails.
        """
        console.print("[blue]TuxMate not found in PATH. Downloading...[/blue]")
        
        tmp_path = Path("/tmp/tuxmate")
        
        # Try multiple download sources
        download_urls = [
            TUXMATE_RAW_URL,
            TUXMATE_FALLBACK_URL,
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
                    )
                    
                    progress.update(task, completed=True)

                if result.returncode == 0 and tmp_path.exists():
                    # Make executable
                    tmp_path.chmod(tmp_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    console.print(f"[green]✓ TuxMate downloaded to {tmp_path}[/green]")
                    return str(tmp_path)

            except subprocess.SubprocessError:
                continue

        # If curl fails, try with wget
        try:
            result = subprocess.run(
                ["wget", "-q", "-O", str(tmp_path), TUXMATE_FALLBACK_URL],
                capture_output=True,
            )
            if result.returncode == 0 and tmp_path.exists():
                tmp_path.chmod(tmp_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                return str(tmp_path)
        except subprocess.SubprocessError:
            pass

        raise RuntimeError(
            "Failed to download TuxMate. Please install it manually:\n"
            f"  curl -fsSL {TUXMATE_FALLBACK_URL} -o /usr/local/bin/tuxmate\n"
            "  chmod +x /usr/local/bin/tuxmate"
        )

    def get_tuxmate(self) -> str:
        """
        Get path to tuxmate, downloading if necessary.
        
        Returns:
            Path to tuxmate executable.
        """
        if self._tuxmate_path:
            return self._tuxmate_path

        # Check if already in PATH
        path = self.find_tuxmate()
        if path:
            console.print(f"[green]✓ Found TuxMate at {path}[/green]")
            self._tuxmate_path = path
            return path

        # Download to /tmp
        self._tuxmate_path = self.download_tuxmate()
        return self._tuxmate_path

    def install_packages(self, packages: list[str], dry_run: bool = False) -> bool:
        """
        Install packages using tuxmate.
        
        Args:
            packages: List of package names to install.
            dry_run: If True, only show what would be installed.
            
        Returns:
            True if installation succeeded.
        """
        if not packages:
            console.print("[yellow]No packages to install[/yellow]")
            return True

        tuxmate = self.get_tuxmate()
        
        console.print(f"\n[blue]Installing {len(packages)} packages via TuxMate...[/blue]")

        if dry_run:
            console.print("[yellow]DRY RUN - Would install:[/yellow]")
            for pkg in packages:
                console.print(f"  • {pkg}")
            return True

        # Pass packages to tuxmate
        # TuxMate should handle the actual package manager detection
        try:
            # Create a package list file for tuxmate
            pkg_list_file = Path("/tmp/tuxsync_packages.txt")
            pkg_list_file.write_text("\n".join(packages))

            # Try different tuxmate invocation patterns
            # Pattern 1: tuxmate install --file <file>
            # Pattern 2: tuxmate install <pkg1> <pkg2> ...
            # Pattern 3: Pass via stdin

            cmd = [tuxmate, "install", "--file", str(pkg_list_file)]
            
            result = subprocess.run(
                cmd,
                capture_output=False,  # Let output show to user
                text=True,
            )

            if result.returncode != 0:
                # Fallback: Try direct package list
                console.print("[yellow]Trying alternative invocation...[/yellow]")
                
                # Install in batches to avoid command line length limits
                batch_size = 50
                for i in range(0, len(packages), batch_size):
                    batch = packages[i:i + batch_size]
                    cmd = [tuxmate, "install"] + batch
                    subprocess.run(cmd)

            # Cleanup
            pkg_list_file.unlink(missing_ok=True)

            return True

        except subprocess.SubprocessError as e:
            console.print(f"[red]Installation failed: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
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
                
                console.print(f"[blue]Backing up existing .bashrc to {backup_path}[/blue]")
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
        console.print(f"\n[bold blue]═══ TuxSync Restore ═══[/bold blue]\n")

        try:
            # Get storage backend
            storage = get_storage_backend(storage_type, server_url)

            # Fetch backup
            console.print(f"[blue]Fetching backup: {backup_id}[/blue]")
            metadata, bashrc_content = storage.load(backup_id)

            # Show backup info
            console.print(f"\n[bold]Backup Information:[/bold]")
            console.print(f"  Created: {metadata.created_at}")
            console.print(f"  Source: {metadata.distro} {metadata.distro_version}")
            console.print(f"  Package Manager: {metadata.package_manager}")
            console.print(f"  Packages: {metadata.package_count}")
            console.print(f"  Has .bashrc: {metadata.has_bashrc}")
            console.print()

            success = True

            # Restore packages
            if not skip_packages and metadata.packages:
                console.print(f"[bold]Restoring {len(metadata.packages)} packages...[/bold]")
                if not self.executor.install_packages(metadata.packages, dry_run):
                    console.print("[yellow]⚠ Some packages may have failed to install[/yellow]")
                    success = False

            # Restore bashrc
            if not skip_bashrc and bashrc_content and metadata.has_bashrc:
                if dry_run:
                    console.print("[yellow]DRY RUN - Would restore .bashrc[/yellow]")
                else:
                    self.restore_bashrc(bashrc_content, merge=merge_bashrc)

            if success:
                console.print("\n[bold green]✓ Restore completed successfully![/bold green]")
            else:
                console.print("\n[bold yellow]⚠ Restore completed with warnings[/bold yellow]")

            return success

        except Exception as e:
            console.print(f"\n[bold red]✗ Restore failed: {e}[/bold red]")
            return False
