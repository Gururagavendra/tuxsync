"""
Utilities for TuxSync.
Helper functions for gum integration and shell operations.
"""

import subprocess
import shutil
from typing import Optional


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
            "gum", "spin",
            "--spinner", "dot",
            "--title", title,
            "--",
        ] + command
        
        result = subprocess.run(full_cmd)
        return result.returncode == 0
    else:
        print(f"{title}...")
        result = subprocess.run(command)
        return result.returncode == 0
