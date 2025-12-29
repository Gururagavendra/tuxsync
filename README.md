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
- **Loose Coupling** - Uses [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) as external executor
- **Smart Scanning** - Only backs up user-installed packages, filters out libraries
- **Magic Restore** - One-liner command to restore your setup on any Linux machine

See [Usage](#usage) section below for detailed commands.

## Installation

```bash
pip install tuxsync --upgrade
```

## Usage

### Create a Backup

```bash
# Interactive mode (recommended)
tuxsync backup

# Skip bashrc backup
tuxsync backup --no-bashrc

# Direct to GitHub (non-interactive)
tuxsync backup --github --non-interactive
```

### Restore on New Machine

```bash
# Using the magic command (shown after backup, even tuxsync installation not needed on new machine, making it 0 friction )
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>

# Or install TuxSync and restore
tuxsync restore <GIST_ID>

# Dry run to see what would happen
tuxsync restore <GIST_ID> --dry-run

# Skip package installation, only restore bashrc
tuxsync restore <GIST_ID> --skip-packages
```

### List Backups

```bash
tuxsync list
```

## Requirements

- Python 3.10+
- [GitHub CLI (gh)](https://cli.github.com/) - For GitHub Gist storage
- [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) - Auto-downloaded when needed
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
- **TuxSync** - The Brain (orchestrates backup/restore workflow)
- **tuxmate-cli** - The Hands (handles cross-distro package installation using [tuxmate's](https://github.com/abusoww/tuxmate) curated package database)
- **Loose coupling** - Both tools work independently

For detailed architecture and technical specifications, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Status: Work in Progress

> **Early Development**: TuxSync is actively being developed.

### Implemented

- Package scanning (apt, dnf, pacman)
- GitHub Gist storage
- bashrc backup/restore
- tuxmate-cli integration
- Dry-run mode

### Later

- [ ] Config file syncing (dotfiles) - Basically syncing all your dotfiles, not just bashrc
- [ ] Incremental backups - Only backup changes since last backup
- [ ] Profile versioning - Keep multiple versions/snapshots with timestamps

## Custom Server Support

Want to host backups on your own server instead of GitHub? See [Custom Server API](docs/CUSTOM_SERVER.md) for implementation details.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

GPL-3.0 License - See [LICENSE](LICENSE) for details.

## Credits

- Package restoration powered by [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli)
- Package database from [tuxmate](https://github.com/abusoww/tuxmate) by [@abusoww](https://github.com/abusoww) - curated collection of 150+ Linux applications
