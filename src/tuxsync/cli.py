"""
CLI module for TuxSync.
Main entry point with backup and restore commands.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .scanner import PackageScanner
from .storage import get_storage_backend, BackupResult
from .restore import RestoreManager
from .utils import gum_choose, gum_confirm, gum_input

console = Console()


def print_banner():
    """Print the TuxSync banner."""
    banner = """
╔════════════════════════════════════════╗
║          TuxSync v{}                ║
║   Profile Sync for Linux Users         ║
╚════════════════════════════════════════╝
    """.format(__version__.ljust(5))
    console.print(Panel(banner, style="blue"))


def print_restore_command(result: BackupResult):
    """Print the magic restore command."""
    console.print("\n[bold green]═══ Backup Complete! ═══[/bold green]\n")
    console.print("[bold]Your Magic Restore Command:[/bold]")
    console.print()
    console.print(Panel(result.restore_command, title="Copy this command", style="cyan"))
    console.print()
    console.print(f"[dim]Backup ID: {result.backup_id}[/dim]")
    console.print("[dim]Run this command on any Linux machine to restore your setup![/dim]")


@click.group()
@click.version_option(version=__version__, prog_name="TuxSync")
def cli():
    """
    TuxSync - Profile Sync for Linux Users
    
    Backup and restore your packages and configurations across machines.
    """
    pass


@cli.command()
@click.option(
    "--no-bashrc",
    is_flag=True,
    default=False,
    help="Skip backing up ~/.bashrc",
)
@click.option(
    "--github",
    "storage_type",
    flag_value="github",
    help="Store backup on GitHub Gist",
)
@click.option(
    "--server",
    "server_url",
    default=None,
    help="Use custom server URL for storage",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Run without interactive prompts (requires --github or --server)",
)
def backup(
    no_bashrc: bool,
    storage_type: Optional[str],
    server_url: Optional[str],
    non_interactive: bool,
):
    """
    Create a backup of installed packages and configurations.
    
    Scans your system for user-installed packages and optionally
    backs up your ~/.bashrc file.
    """
    print_banner()
    console.print("[bold]Starting Backup...[/bold]\n")

    # Phase 1: Scanner
    scanner = PackageScanner(include_bashrc=not no_bashrc)
    scan_result = scanner.scan()

    if not scan_result.packages:
        console.print("[yellow]Warning: No packages found to backup[/yellow]")
        if not gum_confirm("Continue anyway?"):
            console.print("[red]Backup cancelled[/red]")
            sys.exit(1)

    # Show summary
    console.print(f"\n[bold]Scan Summary:[/bold]")
    console.print(f"  Distro: {scan_result.distro} {scan_result.distro_version}")
    console.print(f"  Packages: {len(scan_result.packages)}")
    console.print(f"  Bashrc: {'✓' if scan_result.bashrc_content else '✗'}")
    console.print()

    # Phase 2: Storage selection
    if not storage_type and not server_url:
        if non_interactive:
            console.print("[red]Error: --github or --server required in non-interactive mode[/red]")
            sys.exit(1)
        
        choice = gum_choose(
            "Where would you like to store your backup?",
            ["GitHub Gist (recommended)", "Custom Server"],
            default="GitHub Gist (recommended)",
        )

        if choice and "GitHub" in choice:
            storage_type = "github"
        elif choice and "Custom" in choice:
            server_url = gum_input(
                "Enter your server URL",
                placeholder="https://your-server.com",
            )
            if not server_url:
                console.print("[red]Server URL required[/red]")
                sys.exit(1)
            storage_type = "custom"
        else:
            console.print("[red]Backup cancelled[/red]")
            sys.exit(1)

    # Determine final storage type
    if server_url:
        storage_type = "custom"
    elif not storage_type:
        storage_type = "github"

    # Create storage backend and save
    try:
        storage = get_storage_backend(storage_type, server_url)
        result = storage.save(scan_result)

        if result.success:
            print_restore_command(result)
        else:
            console.print(f"\n[bold red]Backup failed: {result.error}[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("backup_id")
@click.option(
    "--server",
    "server_url",
    default=None,
    help="Custom server URL (if not using GitHub)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without making changes",
)
@click.option(
    "--skip-packages",
    is_flag=True,
    default=False,
    help="Skip package installation",
)
@click.option(
    "--skip-bashrc",
    is_flag=True,
    default=False,
    help="Skip .bashrc restoration",
)
@click.option(
    "--merge-bashrc",
    is_flag=True,
    default=False,
    help="Merge .bashrc instead of replacing",
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompts",
)
def restore(
    backup_id: str,
    server_url: Optional[str],
    dry_run: bool,
    skip_packages: bool,
    skip_bashrc: bool,
    merge_bashrc: bool,
    yes: bool,
):
    """
    Restore packages and configurations from a backup.
    
    BACKUP_ID is the Gist ID or backup identifier from your backup command.
    """
    print_banner()

    # Determine storage type
    storage_type = "custom" if server_url else "github"

    # Confirmation (unless --yes or --dry-run)
    if not yes and not dry_run:
        console.print(f"[yellow]This will restore packages from backup: {backup_id}[/yellow]")
        if not gum_confirm("Continue with restore?", default=True):
            console.print("[red]Restore cancelled[/red]")
            sys.exit(1)

    # Perform restore
    manager = RestoreManager()
    success = manager.restore(
        backup_id=backup_id,
        storage_type=storage_type,
        server_url=server_url,
        dry_run=dry_run,
        skip_packages=skip_packages,
        skip_bashrc=skip_bashrc,
        merge_bashrc=merge_bashrc,
    )

    sys.exit(0 if success else 1)


@cli.command()
@click.option(
    "--server",
    "server_url",
    default=None,
    help="Custom server URL (if not using GitHub)",
)
def list(server_url: Optional[str]):
    """
    List available backups.
    
    Shows your backups stored on GitHub Gists or custom server.
    """
    print_banner()
    
    if server_url:
        console.print("[yellow]Custom server listing not yet implemented[/yellow]")
        return

    # List GitHub Gists
    console.print("[blue]Fetching your TuxSync backups from GitHub...[/blue]\n")

    import subprocess
    try:
        result = subprocess.run(
            ["gh", "gist", "list", "--limit", "20"],
            capture_output=True,
            text=True,
            check=True,
        )

        gists = result.stdout.strip().split("\n")
        tuxsync_gists = [g for g in gists if "TuxSync" in g or "tuxsync" in g]

        if tuxsync_gists:
            console.print("[bold]Your TuxSync Backups:[/bold]\n")
            for gist in tuxsync_gists:
                parts = gist.split("\t")
                if len(parts) >= 3:
                    gist_id = parts[0]
                    desc = parts[1] if len(parts) > 1 else "No description"
                    console.print(f"  [cyan]{gist_id}[/cyan]")
                    console.print(f"    {desc}\n")
        else:
            console.print("[yellow]No TuxSync backups found[/yellow]")
            console.print("[dim]Create one with: tuxsync backup[/dim]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to list gists: {e.stderr}[/red]")
    except FileNotFoundError:
        console.print("[red]GitHub CLI (gh) not found. Please install it.[/red]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
