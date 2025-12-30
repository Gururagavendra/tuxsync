<div align="center">
  <h1>TuxSync</h1>
  <p><strong>PROFILE SYNC FOR YOUR LINUX MACHINES</strong></p>

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
[![PyPI](https://img.shields.io/pypi/v/tuxsync?style=for-the-badge)](https://pypi.org/project/tuxsync/)
[![Python](https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://github.com/Gururagavendra/tuxsync)
[![License](https://img.shields.io/badge/license-GPL--3.0-yellow?style=for-the-badge)](LICENSE)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-green?style=for-the-badge)]()

</div>

## Migration Assistant for Linux

Backup and restore your packages and configurations across Linux machines - like Apple's Migration Assistant or Chrome Sync, but **private, open-source, and under your control**. Your data stays in your GitHub account, not some company's servers.

## Features

```bash
# Backup your files from your old machine
tuxsync backup

# Restore on new machine
pip install tuxsync
tuxsync restore <GIST_ID>

# List your backups
tuxsync list
```

- **Multi-Distro Support** - Ubuntu/Debian (apt), Fedora (dnf), and Arch (pacman)
- **Privacy First** - GitHub Gists (convenient) or your own custom server (private)
- **Chezmoi Integration** - Optional comprehensive dotfile management with encryption support
- **Loose Coupling** - Uses [tuxmate](https://github.com/abusoww/tuxmate), [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli), and [chezmoi](https://github.com/twpayne/chezmoi) as external executors
- **Smart Scanning** - Only backs up user-installed packages, filters out libraries
- **Magic Restore** - One-liner command to restore your setup on any Linux machine

See [Usage](#usage) section below for detailed commands.

## Installation

```bash
pip install tuxsync --upgrade
```

## Usage

### Quick Start

```bash
# Backup your current system
tuxsync backup

# Restore on a new machine
tuxsync restore <GIST_ID>
```

### Basic Backup (Packages Only)

```bash
# Interactive mode (recommended)
tuxsync backup

# Non-interactive mode
tuxsync backup --github --non-interactive
```

**What happens:**
1. Scans your system for user-installed packages (filters out libraries)
2. Backs up your `~/.bashrc` file
3. Uploads to GitHub Gist (private by default)
4. Gives you a magic restore command

### Full Backup (Packages + ALL Dotfiles)

```bash
# Backup everything with chezmoi integration
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles
```

**What happens:**
1. Backs up all packages (same as basic)
2. **Auto-installs chezmoi** if not present
3. Backs up **ALL your dotfiles** to a GitHub repo:
   - `.bashrc`, `.zshrc`, `.vimrc`, `.gitconfig`
   - All configs in `~/.config/` (nvim, i3, tmux, etc.)
   - SSH configs, custom scripts, everything!
4. Commits and pushes to your dotfiles repository

### Basic Restore (Packages Only)

```bash
# Using the magic one-liner (no installation needed!)
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>

# Or install TuxSync first
pip install tuxsync
tuxsync restore <GIST_ID>
```

**What happens:**
1. Downloads package list from GitHub Gist
2. Installs packages using [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) (cross-distro magic!)
3. Restores your `.bashrc` file

### Full Restore (Packages + Dotfiles)

```bash
tuxsync restore <GIST_ID> --use-chezmoi --chezmoi-repo username/dotfiles
```

**What happens:**
1. Restores all packages (same as basic)
2. **Auto-installs chezmoi** if not present
3. Clones your dotfiles repository
4. Applies all dotfiles system-wide
5. Your entire environment is restored!

### Advanced Options

```bash
# Dry run (see what would happen without making changes)
tuxsync restore <GIST_ID> --dry-run

# Skip specific components
tuxsync backup --no-bashrc                    # Skip .bashrc backup
tuxsync restore <GIST_ID> --skip-packages     # Only restore configs
tuxsync restore <GIST_ID> --skip-bashrc       # Only restore packages

# Merge bashrc instead of replacing
tuxsync restore <GIST_ID> --merge-bashrc

# Non-interactive mode (for automation)
tuxsync backup --github --non-interactive
tuxsync restore <GIST_ID> --yes

# List your backups
tuxsync list
```

### Real-World Scenarios

**Scenario 1: New Laptop (Basic)**
```bash
# Old laptop
$ tuxsync backup
# ✓ Backup ID: abc123def456

# New laptop (any distro!)
$ pip install tuxsync
$ tuxsync restore abc123def456
# ✓ All packages installed!
```

**Scenario 2: New Laptop (Full Setup)**
```bash
# Old laptop
$ tuxsync backup --use-chezmoi --chezmoi-repo myusername/dotfiles

# New laptop
$ pip install tuxsync
$ tuxsync restore abc123def456 --use-chezmoi --chezmoi-repo myusername/dotfiles
# ✓ Packages + entire dotfile setup restored!
```

**Scenario 3: Distro Hopping (Ubuntu → Arch)**
```bash
# On Ubuntu
$ tuxsync backup --use-chezmoi --chezmoi-repo user/dotfiles

# Switch to Arch Linux
$ pip install tuxsync
$ tuxsync restore abc123def456 --use-chezmoi --chezmoi-repo user/dotfiles
# ✓ TuxSync translates apt packages to pacman equivalents!
```

### What Gets Backed Up

| Component | Basic Backup | With `--use-chezmoi` |
|-----------|-------------|----------------------|
| User-installed packages | ✅ | ✅ |
| System libraries | ❌ (auto-filtered) | ❌ |
| `~/.bashrc` | ✅ | ✅ |
| All dotfiles (`~/.vimrc`, `~/.gitconfig`, etc.) | ❌ | ✅ |
| Entire `~/.config/` directory | ❌ | ✅ |
| SSH configs | ❌ | ✅ (optional) |
| Encrypted secrets | ❌ | ✅ (chezmoi supports) |

## Requirements

- Python 3.10+
- [GitHub CLI (gh)](https://cli.github.com/) - For GitHub Gist storage
- [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) - Auto-downloaded when needed
- [chezmoi](https://github.com/twpayne/chezmoi) - Auto-installed when using `--use-chezmoi`
- [gum](https://github.com/charmbracelet/gum) (optional) - For interactive menus

## Development

```bash
git clone https://github.com/Gururagavendra/tuxsync.git
cd tuxsync
uv sync
./tuxsync.sh help
```

## How It Works

TuxSync creates a backup containing your package list and bashrc, stored as a private GitHub Gist. The restore process fetches this backup and uses [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) to install packages across different Linux distributions.

**Architecture:**
- **TuxSync** - The Orchestrator (coordinates backup/restore workflow)
- **tuxmate-cli** - Package Manager (handles cross-distro package installation using [tuxmate's](https://github.com/abusoww/tuxmate) curated package database)
- **chezmoi** - Dotfile Manager (optional integration for comprehensive dotfile syncing)
- **Loose coupling** - All tools work independently, TuxSync orchestrates them

For detailed architecture and technical specifications, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Status: Work in Progress

> **Early Development**: TuxSync is actively being developed.

### Implemented

- ✅ Package scanning (apt, dnf, pacman)
- ✅ GitHub Gist storage
- ✅ bashrc backup/restore
- ✅ tuxmate-cli integration
- ✅ Dry-run mode
- ✅ **Chezmoi integration** - Comprehensive dotfile management

### Later

- [ ] Incremental backups - Only backup changes since last backup
- [ ] Profile versioning - Keep multiple versions/snapshots with timestamps
- [ ] Custom backup schedules and automation

## Custom Server Support

Want to host backups on your own server instead of GitHub? See [Custom Server API](docs/CUSTOM_SERVER.md) for implementation details.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

GPL-3.0 License - See [LICENSE](LICENSE) for details.

## Credits

- Package restoration powered by [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli)
- Package database from [tuxmate](https://github.com/abusoww/tuxmate) by [@abusoww](https://github.com/abusoww) - curated collection of 150+ Linux applications
