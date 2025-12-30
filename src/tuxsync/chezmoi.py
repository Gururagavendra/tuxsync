"""Chezmoi integration for dotfile management.

This module handles optional integration with chezmoi for comprehensive
dotfile backup and restoration. Following TuxSync's loose coupling philosophy,
chezmoi is treated as an external executor that can be swapped or omitted.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .utils import run_command


class ChezmoiManager:
    """Manages chezmoi installation and interaction."""

    def __init__(self):
        """Initialize the Chezmoi manager."""
        self.chezmoi_bin = self._find_chezmoi()

    def _find_chezmoi(self) -> Optional[str]:
        """Find chezmoi binary in PATH.

        Returns:
            Path to chezmoi binary, or None if not found
        """
        return shutil.which("chezmoi")

    def is_installed(self) -> bool:
        """Check if chezmoi is installed.

        Returns:
            True if chezmoi is available, False otherwise
        """
        return self.chezmoi_bin is not None

    def install(self) -> bool:
        """Install chezmoi using the official install script.

        Returns:
            True if installation succeeded, False otherwise
        """
        print("📦 Installing chezmoi...")

        install_cmd = 'sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin'

        try:
            run_command(install_cmd, shell=True)
            # Update the binary path after installation
            self.chezmoi_bin = shutil.which("chezmoi") or str(
                Path.home() / ".local/bin/chezmoi"
            )
            print("✓ chezmoi installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install chezmoi: {e}")
            return False

    def init_repo(self, repo_url: str) -> bool:
        """Initialize chezmoi with a dotfiles repository.

        Args:
            repo_url: GitHub repository URL for dotfiles

        Returns:
            True if initialization succeeded, False otherwise
        """
        if not self.is_installed():
            print("✗ chezmoi is not installed")
            return False

        try:
            print(f"🔧 Initializing chezmoi with {repo_url}")
            run_command([self.chezmoi_bin, "init", repo_url])
            print("✓ chezmoi initialized")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to initialize chezmoi: {e}")
            return False

    def apply(self, dry_run: bool = False) -> bool:
        """Apply dotfiles from chezmoi.

        Args:
            dry_run: If True, only show what would be done

        Returns:
            True if apply succeeded, False otherwise
        """
        if not self.is_installed():
            print("✗ chezmoi is not installed")
            return False

        try:
            cmd = [self.chezmoi_bin, "apply"]
            if dry_run:
                cmd.append("--dry-run")
                print("🔍 Dry run - showing what would be applied:")
            else:
                print("📝 Applying dotfiles...")

            run_command(cmd)
            print("✓ Dotfiles applied" if not dry_run else "")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to apply dotfiles: {e}")
            return False

    def get_source_dir(self) -> Optional[Path]:
        """Get the chezmoi source directory path.

        Returns:
            Path to chezmoi source directory, or None if not initialized
        """
        if not self.is_installed():
            return None

        try:
            result = subprocess.run(
                [self.chezmoi_bin, "source-path"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None

    def add_file(self, file_path: str) -> bool:
        """Add a file to chezmoi management.

        Args:
            file_path: Path to the file to add

        Returns:
            True if file was added, False otherwise
        """
        if not self.is_installed():
            print("✗ chezmoi is not installed")
            return False

        try:
            print(f"➕ Adding {file_path} to chezmoi")
            run_command([self.chezmoi_bin, "add", file_path])
            print(f"✓ Added {file_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to add {file_path}: {e}")
            return False

    def git_push(self) -> bool:
        """Push chezmoi changes to remote repository.

        Returns:
            True if push succeeded (or no changes to push), False on error
        """
        source_dir = self.get_source_dir()
        if not source_dir:
            print("✗ chezmoi source directory not found")
            return False

        try:
            print("📤 Pushing dotfiles to remote repository...")
            # Run git commands in the chezmoi source directory
            run_command(["git", "add", "."], cwd=str(source_dir))

            # Check if there are changes to commit
            status_result = run_command(
                ["git", "status", "--porcelain"],
                cwd=str(source_dir),
                capture_output=True,
                check=False,
            )

            if not status_result.stdout.strip():
                print("✓ No changes to push (dotfiles already up to date)")
                return True

            # Commit and push only if there are changes
            run_command(
                ["git", "commit", "-m", "Update dotfiles via tuxsync"],
                cwd=str(source_dir),
            )
            run_command(["git", "push"], cwd=str(source_dir))
            print("✓ Dotfiles pushed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to push dotfiles: {e}")
            return False


def ensure_chezmoi(auto_install: bool = True) -> Optional[ChezmoiManager]:
    """Ensure chezmoi is available, optionally installing it.

    Args:
        auto_install: If True, install chezmoi if not found

    Returns:
        ChezmoiManager instance if available, None otherwise
    """
    manager = ChezmoiManager()

    if manager.is_installed():
        return manager

    if auto_install:
        print("⚠️  chezmoi not found")
        response = input("Install chezmoi for dotfile management? (y/n): ")
        if response.lower() == "y":
            if manager.install():
                return manager

    return None
