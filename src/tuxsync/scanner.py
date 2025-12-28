"""
Scanner module for TuxSync.
Detects package manager and scans for user-installed packages.
"""

import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from rich.console import Console

console = Console()


class PackageManager(Enum):
    """Supported package managers."""
    APT = "apt"
    DNF = "dnf"
    PACMAN = "pacman"
    UNKNOWN = "unknown"


@dataclass
class ScanResult:
    """Result of a system scan."""
    distro: str
    distro_version: str
    package_manager: PackageManager
    packages: list[str] = field(default_factory=list)
    bashrc_content: Optional[str] = None
    errors: list[str] = field(default_factory=list)


class PackageScanner:
    """Scans the system for installed packages and configurations."""

    # Common library prefixes to filter out
    LIB_PREFIXES = (
        "lib", "python3-", "python-", "fonts-", "gir1.2-",
        "libglib", "libgtk", "libx", "libc6", "libstdc++",
    )

    def __init__(self, include_bashrc: bool = True):
        """
        Initialize the scanner.
        
        Args:
            include_bashrc: Whether to include ~/.bashrc content in scan.
        """
        self.include_bashrc = include_bashrc
        self._package_manager: Optional[PackageManager] = None

    def detect_package_manager(self) -> PackageManager:
        """Detect which package manager is available on the system."""
        if self._package_manager:
            return self._package_manager

        pm_commands = [
            (PackageManager.APT, "apt"),
            (PackageManager.DNF, "dnf"),
            (PackageManager.PACMAN, "pacman"),
        ]

        for pm, cmd in pm_commands:
            if shutil.which(cmd):
                self._package_manager = pm
                return pm

        self._package_manager = PackageManager.UNKNOWN
        return PackageManager.UNKNOWN

    def get_distro_info(self) -> tuple[str, str]:
        """
        Get distribution name and version.
        
        Returns:
            Tuple of (distro_name, distro_version).
        """
        distro = "Unknown"
        version = "Unknown"

        # Try /etc/os-release first (most reliable)
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text()
            for line in content.splitlines():
                if line.startswith("NAME="):
                    distro = line.split("=", 1)[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    version = line.split("=", 1)[1].strip('"')

        return distro, version

    def _get_apt_packages(self) -> list[str]:
        """Get user-installed packages on apt-based systems."""
        packages = []
        try:
            # Use apt-mark showmanual to get manually installed packages
            result = subprocess.run(
                ["apt-mark", "showmanual"],
                capture_output=True,
                text=True,
                check=True,
            )
            all_packages = result.stdout.strip().split("\n")

            # Filter out libraries and common base packages
            packages = [
                pkg for pkg in all_packages
                if pkg and not self._is_library_package(pkg)
            ]
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error getting apt packages: {e}[/red]")
        except FileNotFoundError:
            console.print("[red]apt-mark command not found[/red]")

        return sorted(packages)

    def _get_dnf_packages(self) -> list[str]:
        """Get user-installed packages on dnf-based systems."""
        packages = []
        try:
            # Get packages installed by user (not as dependencies)
            result = subprocess.run(
                ["dnf", "repoquery", "--userinstalled", "--qf", "%{name}"],
                capture_output=True,
                text=True,
                check=True,
            )
            all_packages = result.stdout.strip().split("\n")

            packages = [
                pkg for pkg in all_packages
                if pkg and not self._is_library_package(pkg)
            ]
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error getting dnf packages: {e}[/red]")
        except FileNotFoundError:
            console.print("[red]dnf command not found[/red]")

        return sorted(packages)

    def _get_pacman_packages(self) -> list[str]:
        """Get user-installed packages on pacman-based systems."""
        packages = []
        try:
            # Get explicitly installed packages (not dependencies)
            result = subprocess.run(
                ["pacman", "-Qe", "-q"],
                capture_output=True,
                text=True,
                check=True,
            )
            all_packages = result.stdout.strip().split("\n")

            packages = [
                pkg for pkg in all_packages
                if pkg and not self._is_library_package(pkg)
            ]
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error getting pacman packages: {e}[/red]")
        except FileNotFoundError:
            console.print("[red]pacman command not found[/red]")

        return sorted(packages)

    def _is_library_package(self, package_name: str) -> bool:
        """
        Check if a package is likely a library.
        
        Args:
            package_name: Name of the package.
            
        Returns:
            True if the package appears to be a library.
        """
        pkg_lower = package_name.lower()
        return any(pkg_lower.startswith(prefix) for prefix in self.LIB_PREFIXES)

    def get_packages(self) -> list[str]:
        """
        Get list of user-installed packages.
        
        Returns:
            List of package names.
        """
        pm = self.detect_package_manager()

        package_getters = {
            PackageManager.APT: self._get_apt_packages,
            PackageManager.DNF: self._get_dnf_packages,
            PackageManager.PACMAN: self._get_pacman_packages,
        }

        getter = package_getters.get(pm)
        if getter:
            return getter()

        console.print("[red]No supported package manager found[/red]")
        return []

    def get_bashrc_content(self) -> Optional[str]:
        """
        Read ~/.bashrc content.
        
        Returns:
            Content of ~/.bashrc or None if not found.
        """
        bashrc_path = Path.home() / ".bashrc"
        
        if bashrc_path.exists():
            try:
                return bashrc_path.read_text()
            except PermissionError:
                console.print("[yellow]Warning: Cannot read ~/.bashrc[/yellow]")
                return None
        
        return None

    def scan(self) -> ScanResult:
        """
        Perform a full system scan.
        
        Returns:
            ScanResult with all collected information.
        """
        console.print("[blue]Scanning system...[/blue]")
        
        distro, version = self.get_distro_info()
        pm = self.detect_package_manager()
        
        console.print(f"  Detected: [green]{distro} {version}[/green]")
        console.print(f"  Package Manager: [green]{pm.value}[/green]")
        
        console.print("  Scanning packages...")
        packages = self.get_packages()
        console.print(f"  Found [green]{len(packages)}[/green] user-installed packages")
        
        bashrc_content = None
        if self.include_bashrc:
            console.print("  Reading ~/.bashrc...")
            bashrc_content = self.get_bashrc_content()
            if bashrc_content:
                console.print("  [green]✓[/green] ~/.bashrc captured")
            else:
                console.print("  [yellow]⚠[/yellow] ~/.bashrc not found or empty")
        
        return ScanResult(
            distro=distro,
            distro_version=version,
            package_manager=pm,
            packages=packages,
            bashrc_content=bashrc_content,
        )
