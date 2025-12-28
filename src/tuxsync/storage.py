"""
Storage module for TuxSync.
Handles backup storage to GitHub Gists or custom servers.
"""

import datetime
import subprocess
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import requests
import yaml
from rich.console import Console

from .scanner import ScanResult

console = Console()


@dataclass
class BackupMetadata:
    """Metadata for a TuxSync backup."""

    version: str
    created_at: str
    distro: str
    distro_version: str
    package_manager: str
    package_count: int
    packages: list[str]
    has_bashrc: bool

    @classmethod
    def from_scan_result(
        cls, scan: ScanResult, version: str = "1.0"
    ) -> "BackupMetadata":
        """Create metadata from a scan result."""
        return cls(
            version=version,
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
            distro=scan.distro,
            distro_version=scan.distro_version,
            package_manager=scan.package_manager.value,
            package_count=len(scan.packages),
            packages=scan.packages,
            has_bashrc=scan.bashrc_content is not None,
        )

    def to_yaml(self) -> str:
        """Convert metadata to YAML string."""
        return yaml.dump(asdict(self), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "BackupMetadata":
        """Create metadata from YAML string."""
        data = yaml.safe_load(yaml_content)
        return cls(**data)


@dataclass
class BackupResult:
    """Result of a backup operation."""

    success: bool
    backup_id: str
    storage_type: str
    restore_command: str
    error: Optional[str] = None


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, scan: ScanResult) -> BackupResult:
        """Save scan result to storage."""
        pass

    @abstractmethod
    def load(self, backup_id: str) -> tuple[BackupMetadata, Optional[str]]:
        """
        Load backup from storage.

        Returns:
            Tuple of (metadata, bashrc_content).
        """
        pass


class GitHubStorage(StorageBackend):
    """Storage backend using GitHub Gists via gh CLI."""

    def __init__(self):
        self._check_gh_installed()

    def _check_gh_installed(self) -> None:
        """Check if gh CLI is installed."""
        try:
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "GitHub CLI (gh) is not installed. "
                "Please install it: https://cli.github.com/"
            )

    def check_auth_status(self) -> bool:
        """Check if user is authenticated with GitHub."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    def authenticate(self) -> bool:
        """Trigger GitHub authentication flow."""
        console.print("[blue]Starting GitHub authentication...[/blue]")
        try:
            # Run interactively so user can complete auth
            result = subprocess.run(
                ["gh", "auth", "login", "--web", "-p", "https"],
                check=False,
            )
            return result.returncode == 0
        except subprocess.SubprocessError as e:
            console.print(f"[red]Authentication failed: {e}[/red]")
            return False

    def save(self, scan: ScanResult) -> BackupResult:
        """Save scan result as a secret GitHub Gist."""
        # Check authentication
        if not self.check_auth_status():
            console.print("[yellow]Not logged in to GitHub[/yellow]")
            if not self.authenticate():
                return BackupResult(
                    success=False,
                    backup_id="",
                    storage_type="github",
                    restore_command="",
                    error="GitHub authentication failed",
                )

        console.print("[blue]Creating GitHub Gist...[/blue]")

        # Prepare metadata
        metadata = BackupMetadata.from_scan_result(scan)
        yaml_content = metadata.to_yaml()

        # Create temporary files for gist
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write tuxsync.yaml
            yaml_file = tmpdir_path / "tuxsync.yaml"
            yaml_file.write_text(yaml_content)

            # Build gist command
            files = [str(yaml_file)]

            # Write .bashrc if available
            if scan.bashrc_content:
                bashrc_file = tmpdir_path / "bashrc"
                bashrc_file.write_text(scan.bashrc_content)
                files.append(str(bashrc_file))

            # Create secret gist
            try:
                description = (
                    f"TuxSync backup - {scan.distro} {scan.distro_version} - "
                    f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )

                cmd = [
                    "gh",
                    "gist",
                    "create",
                    "--desc",
                    description,
                    "--public=false",  # Secret gist
                ] + files

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Parse gist URL to get ID
                gist_url = result.stdout.strip()
                gist_id = gist_url.split("/")[-1]

                restore_cmd = (
                    f"curl -sL https://raw.githubusercontent.com/"
                    f"Gururagavendra/tuxsync/main/restore.sh | bash -s -- {gist_id}"
                )

                console.print("[green]✓ Backup created successfully![/green]")
                console.print(f"  Gist URL: {gist_url}")

                return BackupResult(
                    success=True,
                    backup_id=gist_id,
                    storage_type="github",
                    restore_command=restore_cmd,
                )

            except subprocess.CalledProcessError as e:
                return BackupResult(
                    success=False,
                    backup_id="",
                    storage_type="github",
                    restore_command="",
                    error=f"Failed to create gist: {e.stderr}",
                )

    def load(self, backup_id: str) -> tuple[BackupMetadata, Optional[str]]:
        """Load backup from a GitHub Gist."""
        console.print(f"[blue]Fetching backup {backup_id}...[/blue]")

        try:
            # Get gist files
            result = subprocess.run(
                ["gh", "gist", "view", backup_id, "--raw", "-f", "tuxsync.yaml"],
                capture_output=True,
                text=True,
                check=True,
            )
            yaml_content = result.stdout
            metadata = BackupMetadata.from_yaml(yaml_content)

            # Try to get bashrc
            bashrc_content = None
            if metadata.has_bashrc:
                try:
                    result = subprocess.run(
                        ["gh", "gist", "view", backup_id, "--raw", "-f", "bashrc"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    bashrc_content = result.stdout
                except subprocess.CalledProcessError:
                    console.print("[yellow]Warning: Could not fetch bashrc[/yellow]")

            return metadata, bashrc_content

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to fetch gist: {e.stderr}")


class CustomServerStorage(StorageBackend):
    """Storage backend using a custom server."""

    def __init__(self, server_url: str):
        """
        Initialize custom server storage.

        Args:
            server_url: Base URL of the storage server.
        """
        self.server_url = server_url.rstrip("/")

    def save(self, scan: ScanResult) -> BackupResult:
        """Save scan result to custom server."""
        console.print(f"[blue]Uploading to {self.server_url}...[/blue]")

        metadata = BackupMetadata.from_scan_result(scan)

        payload = {
            "metadata": asdict(metadata),
            "bashrc": scan.bashrc_content,
        }

        try:
            response = requests.post(
                f"{self.server_url}/api/backup",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            backup_id = data.get("backup_id", "unknown")

            restore_cmd = f"tuxsync restore --server {self.server_url} {backup_id}"

            console.print("[green]✓ Backup uploaded successfully![/green]")

            return BackupResult(
                success=True,
                backup_id=backup_id,
                storage_type="custom",
                restore_command=restore_cmd,
            )

        except requests.RequestException as e:
            return BackupResult(
                success=False,
                backup_id="",
                storage_type="custom",
                restore_command="",
                error=f"Failed to upload: {e}",
            )

    def load(self, backup_id: str) -> tuple[BackupMetadata, Optional[str]]:
        """Load backup from custom server."""
        console.print(
            f"[blue]Fetching backup {backup_id} from {self.server_url}...[/blue]"
        )

        try:
            response = requests.get(
                f"{self.server_url}/api/backup/{backup_id}",
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            metadata = BackupMetadata(**data["metadata"])
            bashrc_content = data.get("bashrc")

            return metadata, bashrc_content

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch backup: {e}")


def get_storage_backend(
    storage_type: str,
    server_url: Optional[str] = None,
) -> StorageBackend:
    """
    Get appropriate storage backend.

    Args:
        storage_type: Either "github" or "custom".
        server_url: URL for custom server (required if storage_type is "custom").

    Returns:
        Storage backend instance.
    """
    if storage_type == "github":
        return GitHubStorage()
    elif storage_type == "custom":
        if not server_url:
            raise ValueError("Server URL required for custom storage")
        return CustomServerStorage(server_url)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
