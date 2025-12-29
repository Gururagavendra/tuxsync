"""
Configuration management for TuxSync.
Centralized configuration to avoid hardcoded values.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TuxSyncConfig:
    """TuxSync configuration with sensible defaults."""

    # Repository settings
    github_repo: str = "Gururagavendra/tuxsync"
    tuxmate_cli_repo: str = "Gururagavendra/tuxmate-cli"

    # Network settings
    network_timeout: int = 30
    retry_attempts: int = 3
    retry_backoff_base: float = 2.0

    # Batch settings
    package_batch_size: int = 20
    gist_list_limit: int = 20

    # Paths
    tmp_dir: Path = field(default_factory=lambda: Path("/tmp"))

    @classmethod
    def from_env(cls) -> "TuxSyncConfig":
        """
        Load config from environment variables.

        Environment variables:
            TUXSYNC_GITHUB_REPO: Override default GitHub repo
            TUXSYNC_TUXMATE_REPO: Override TuxMate CLI repo
            TUXSYNC_TIMEOUT: Network timeout in seconds
            TUXSYNC_RETRY_ATTEMPTS: Number of retry attempts
            TUXSYNC_BATCH_SIZE: Package batch size
        """
        config = cls()

        if repo := os.environ.get("TUXSYNC_GITHUB_REPO"):
            config.github_repo = repo

        if tuxmate_repo := os.environ.get("TUXSYNC_TUXMATE_REPO"):
            config.tuxmate_cli_repo = tuxmate_repo

        if timeout := os.environ.get("TUXSYNC_TIMEOUT"):
            try:
                config.network_timeout = int(timeout)
            except ValueError:
                pass

        if retries := os.environ.get("TUXSYNC_RETRY_ATTEMPTS"):
            try:
                config.retry_attempts = int(retries)
            except ValueError:
                pass

        if batch_size := os.environ.get("TUXSYNC_BATCH_SIZE"):
            try:
                config.package_batch_size = int(batch_size)
            except ValueError:
                pass

        return config

    @property
    def restore_script_url(self) -> str:
        """Get restore script URL."""
        return f"https://raw.githubusercontent.com/{self.github_repo}/main/restore.sh"

    @property
    def tuxmate_cli_release_url(self) -> str:
        """Get tuxmate-cli latest release URL."""
        return (
            f"https://github.com/{self.tuxmate_cli_repo}"
            f"/releases/latest/download/tuxmate-cli.sh"
        )

    @property
    def tuxmate_cli_fallback_url(self) -> str:
        """Get tuxmate-cli fallback raw URL."""
        return (
            f"https://raw.githubusercontent.com/{self.tuxmate_cli_repo}"
            f"/main/tuxmate-cli.sh"
        )


# Global config instance (lazy loaded)
_config: Optional[TuxSyncConfig] = None


def get_config() -> TuxSyncConfig:
    """
    Get global configuration instance.

    Returns:
        TuxSyncConfig instance loaded from environment.
    """
    global _config
    if _config is None:
        _config = TuxSyncConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset global config (useful for testing)."""
    global _config
    _config = None
