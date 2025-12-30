"""
Utilities for TuxSync.
Helper functions for gum integration, shell operations, and security.
"""

import logging
import re
import shutil
import subprocess
import time
from typing import Optional

from .config import get_config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def sanitize_backup_id(backup_id: str) -> str:
    """
    Sanitize and validate backup ID to prevent injection attacks.

    GitHub Gist IDs are alphanumeric strings (typically 32 characters).

    Args:
        backup_id: The backup ID to sanitize.

    Returns:
        Sanitized backup ID.

    Raises:
        ValidationError: If backup ID format is invalid.
    """
    if not backup_id:
        raise ValidationError("Backup ID cannot be empty")

    # Strip whitespace
    backup_id = backup_id.strip()

    # GitHub Gist IDs are alphanumeric, typically 20-40 chars
    if not re.match(r"^[a-zA-Z0-9]{8,64}$", backup_id):
        raise ValidationError(
            f"Invalid backup ID format: '{backup_id}'. "
            "Expected alphanumeric string (8-64 characters)."
        )

    return backup_id


def sanitize_url(url: str) -> str:
    """
    Sanitize and validate URL.

    Args:
        url: The URL to sanitize.

    Returns:
        Sanitized URL.

    Raises:
        ValidationError: If URL format is invalid.
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    url = url.strip()

    # Basic URL validation
    # Note: Shell-injection protection should be handled at the call site
    # by passing URLs as subprocess arguments rather than in shell strings
    if not re.match(
        r"^https?://[a-zA-Z0-9][-a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%]+$", url
    ):
        raise ValidationError(f"Invalid URL format: '{url}'")

    return url


def run_command(
    command: list[str] | str,
    shell: bool = False,
    cwd: Optional[str] = None,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a command without retry logic (for simple operations).

    This is a lightweight wrapper for subprocess.run() used by external
    integrations (like chezmoi) that don't need retry logic.

    SECURITY WARNING: When shell=True, the command is executed through the
    shell. Only use shell=True with hardcoded commands, NEVER with user input.
    Prefer passing command as a list of strings with shell=False (default)
    to prevent shell injection attacks.

    Args:
        command: Command to run as list of strings or string (if shell=True).
        shell: Whether to run command through shell. AVOID with user input.
        cwd: Working directory for command execution.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit code.

    Returns:
        CompletedProcess result.

    Raises:
        subprocess.SubprocessError: If command fails and check=True.
    """
    return subprocess.run(
        command,
        shell=shell,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=check,
    )


def run_command_with_retry(
    command: list[str],
    max_attempts: Optional[int] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run command with retry logic and exponential backoff.

    Args:
        command: Command to run as list of strings.
        max_attempts: Maximum retry attempts (default from config).
        timeout: Timeout in seconds (default from config).
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit code.

    Returns:
        CompletedProcess result.

    Raises:
        subprocess.SubprocessError: If all attempts fail.
    """
    config = get_config()
    max_attempts = max_attempts or config.retry_attempts
    timeout = timeout or config.network_timeout

    last_exception: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
            )
            return result

        except subprocess.TimeoutExpired as e:
            last_exception = e
            logger.warning(
                f"Command timed out (attempt {attempt}/{max_attempts}): {command[0]}"
            )

        except subprocess.CalledProcessError as e:
            last_exception = e
            logger.warning(
                f"Command failed (attempt {attempt}/{max_attempts}): "
                f"{command[0]} - exit code {e.returncode}"
            )

        except subprocess.SubprocessError as e:
            last_exception = e
            logger.warning(f"Command error (attempt {attempt}/{max_attempts}): {e}")

        if attempt < max_attempts:
            # Exponential backoff
            sleep_time = config.retry_backoff_base**attempt
            logger.debug(f"Retrying in {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    raise subprocess.SubprocessError(
        f"Command failed after {max_attempts} attempts: {last_exception}"
    )


def gum_available() -> bool:
    """Check if gum is available."""
    return shutil.which("gum") is not None


def gum_confirm(prompt: str, default: bool = False) -> bool:
    """
    Show a confirmation prompt using gum.

    Falls back to basic input if gum is not available.

    Args:
        prompt: The confirmation message.
        default: Default value if gum is not available.

    Returns:
        True if user confirmed.
    """
    if gum_available():
        result = subprocess.run(
            ["gum", "confirm", prompt],
            capture_output=False,
        )
        return result.returncode == 0
    else:
        response = input(f"{prompt} [y/N] ").strip().lower()
        return response in ("y", "yes")


def gum_choose(
    prompt: str,
    choices: list[str],
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Show a selection menu using gum.

    Falls back to numbered selection if gum is not available.

    Args:
        prompt: The prompt message.
        choices: List of choices.
        default: Default selection.

    Returns:
        Selected choice or None if cancelled.
    """
    if not choices:
        return None

    if gum_available():
        cmd = ["gum", "choose", "--header", prompt]
        if default:
            cmd.extend(["--selected", default])
        cmd.extend(choices)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    else:
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")

        try:
            selection = input("\nEnter number: ").strip()
            idx = int(selection) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, IndexError):
            pass

        return default


def gum_input(
    prompt: str,
    placeholder: str = "",
    default: str = "",
) -> str:
    """
    Get text input using gum.

    Falls back to basic input if gum is not available.

    Args:
        prompt: The prompt message.
        placeholder: Placeholder text.
        default: Default value.

    Returns:
        User input string.
    """
    if gum_available():
        cmd = ["gum", "input", "--header", prompt]
        if placeholder:
            cmd.extend(["--placeholder", placeholder])
        if default:
            cmd.extend(["--value", default])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return default
    else:
        prompt_text = f"{prompt}"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "

        response = input(prompt_text).strip()
        return response if response else default


def gum_spin(command: list[str], title: str) -> bool:
    """
    Run a command with a spinner using gum.

    Falls back to running command directly if gum is not available.

    Args:
        command: Command to run.
        title: Spinner title.

    Returns:
        True if command succeeded.
    """
    if gum_available():
        full_cmd = [
            "gum",
            "spin",
            "--spinner",
            "dot",
            "--title",
            title,
            "--",
        ] + command

        result = subprocess.run(full_cmd)
        return result.returncode == 0
    else:
        print(f"{title}...")
        result = subprocess.run(command)
        return result.returncode == 0
