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
# basic backup (apps+packages+bashrc)
tuxsync backup

# full backup (apps+packages+all-dotfiles+config-files+secrets(encrypted))
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles

# Restore on new machine
pip install tuxsync
tuxsync restore <GIST_ID>

# List your backups
tuxsync list
```

- **Multi-Distro Support** - Ubuntu/Debian (apt), Fedora (dnf), and Arch (pacman)
- **Privacy First** - GitHub Gists (convenient) or your own custom server (private)
- **Chezmoi Integration** - Optional comprehensive dotfile management with encryption support ([guide](docs/CHEZMOI_MANAGEMENT.md))
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
3. Initializes chezmoi with your dotfiles repository
4. You can then add your dotfiles manually

💡 **Learn more:**
- [What files are backed up by default?](docs/CHEZMOI_MANAGEMENT.md#understanding-the-defaults)
- [How to add more dotfiles](docs/CHEZMOI_MANAGEMENT.md#adding-files-to-chezmoi)
- [Behind the scenes: Chezmoi Workflow](docs/CHEZMOI_WORKFLOW.md)

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
| All dotfiles (`~/.vimrc`, `~/.gitconfig`, etc.) | ❌ | ✅ (manual) |
| Entire `~/.config/` directory | ❌ | ✅ (manual) |
| SSH configs | ❌ | ✅ (manual, encrypted) |
| Encrypted secrets | ❌ | ✅ (manual, encrypted) |

See [Managing Dotfiles with Chezmoi](docs/CHEZMOI_MANAGEMENT.md) for details on what's automatic vs manual.

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
**DManaging Dotfiles with Chezmoi](docs/CHEZMOI_MANAGEMENT.md) - Complete guide to adding and managing dotfiles
- [Chezmoi Workflow](docs/CHEZMOI_WORKFLOW.md) - Behind-the-scenes commands and processes
- [Backing Up Sensitive Credentials](docs/SECURITY_CREDENTIALS.md) - Security best practices for SSH keys, credentials
- [Architecture Overview](docs/ARCHITECTURE.md) - Technical specifications and design philosophy
- [Chezmoi Workflow](docs/CHEZMOI_WORKFLOW.md) - Detailed explanation of what happens behind the scenes with `--use-chezmoi`
- [Custom Server API](docs/CUSTOM_SERVER.md) - Self-host your backups

For detailed architecture and technical specifications, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Managing Dotfiles with Chezmoi

When using `--use-chezmoi`, TuxSync integrates with [chezmoi](https://www.chezmoi.io/) for comprehensive dotfile management.

### Quick Overview

**⚠️ Important:** Chezmoi does NOT automatically add files - you have full control.

**What's backed up automatically:**
- ✅ Package list (GitHub Gist)
- ✅ `~/.bashrc` (GitHub Gist)

**What you can add manually:**
- Configuration files (`.vimrc`, `.gitconfig`, `.zshrc`)
- Entire directories (`~/.config/nvim`, `~/.config/i3`)
- Sensitive files (SSH keys, credentials) - **with encryption**

### Quick Start

```bash
# Initial backup
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles

# Add dotfiles
chezmoi add ~/.vimrc ~/.gitconfig ~/.config/nvim

# Add encrypted secrets
chezmoi add --encrypt ~/.ssh/id_rsa
chezmoi add --encrypt ~/.docker/config.json

# View managed files
chezmoi managed

# Push changes
cd ~/.local/share/chezmoi && git push
```

📖 **[Complete Guide: Managing Dotfiles with Chezmoi](docs/CHEZMOI_MANAGEMENT.md)**  
Detailed instructions on adding files, encryption setup, exclusions, and troubleshooting.

---

## Backing Up Sensitive Credentials

TuxSync supports backing up sensitive data like **SSH keys, Docker credentials, cloud provider tokens, and more** using encrypted storage via chezmoi integration.

### Quick Overview

```bash
# Step 1: Setup encryption (one-time)
sudo apt install age
age-keygen -o ~/.config/chezmoi/key.txt

# Step 2: Backup with chezmoi
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles

# Step 3: Add encrypted secrets
chezmoi add --encrypt ~/.ssh/id_rsa
chezmoi add --encrypt ~/.docker/config.json

# Step 4: Push to repo
cd ~/.local/share/chezmoi && git push

# On new machine - credentials are automatically restored
tuxsync restore <GIST_ID> --use-chezmoi --chezmoi-repo username/dotfiles
```

**What can be backed up safely:**
- 🔐 SSH private keys (encrypted)
- 🐳 Docker/container registry credentials (encrypted)
- ☁️ Cloud provider credentials - AWS, GCP, Azure (encrypted)
- 🎯 Kubernetes configs (encrypted)
- 🔑 API tokens and secrets (encrypted)

**Important:** All sensitive data is **encrypted before leaving your machine** using [age](https://age-encryption.org/) or GPG encryption. Your secrets are never stored in plain text.

📖 **[Full Guide: Backing Up Sensitive Credentials](docs/SECURITY_CREDENTIALS.md)** - Detailed security guide with best practices, step-by-step instructions, and troubleshooting.

---

## Status: Work in Progress

> **Early Development**: TuxSync is actively being developed.

### Implemented

- ✅ Package scanning (apt, dnf, pacman)
- ✅ GitHub Gist storage
- ✅ bashrc backup/restore
- ✅ tuxmate-cli integration
- ✅ Dry-run mode
- ✅ **Chezmoi integration** - Comprehensive dotfile management
- ✅ **Encrypted secrets support** - SSH keys, credentials, tokens

### Later

- [ ] Sensitive file auto-detection with encryption prompts
- [ ] Credential rotation helper on restore
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
- dotfile management from [chezmoi](https://github.com/twpayne/chezmoi)
