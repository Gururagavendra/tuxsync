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

Backup and restore your packages and configurations across Linux machines - like Apple's Migration Assistant or Chrome Sync, but for your Linux setup.

## Features

```bash
# Backup your system
./tuxsync.sh backup

# Restore on new machine
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>

# List your backups
uv run tuxsync list
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
./tuxsync.sh backup

# Or using uv
uv run tuxsync backup

# Skip bashrc backup
uv run tuxsync backup --no-bashrc

# Direct to GitHub (non-interactive)
uv run tuxsync backup --github --non-interactive
```

### Restore on New Machine

```bash
# Using the magic command (shown after backup)
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>

# Or install TuxSync and restore
uv run tuxsync restore <GIST_ID>

# Dry run to see what would happen
uv run tuxsync restore <GIST_ID> --dry-run

# Skip package installation, only restore bashrc
uv run tuxsync restore <GIST_ID> --skip-packages
```

### List Backups

```bash
uv run tuxsync list
```

## Requirements

- Python 3.10+
- [GitHub CLI (gh)](https://cli.github.com/) - For GitHub Gist storage
- [gum](https://github.com/charmbracelet/gum) (optional) - For pretty terminal menus
- [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) - For cross-distro package installation

The wrapper script (`tuxsync.sh`) will help install missing dependencies.

## Development

```bash
git clone https://github.com/Gururagavendra/tuxsync.git
cd tuxsync
uv sync
./tuxsync.sh help
```

## Architecture

For detailed architecture and design philosophy, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Quick overview:**
- **TuxSync** - The Brain (orchestrates backup/restore workflow)
- **tuxmate-cli** - The Hands (handles cross-distro package installation)
- **Loose coupling** - Both tools work independently

## Backup Structure

TuxSync creates backups with two files:

### tuxsync.yaml

```yaml
version: "1.0"
created_at: "2024-12-28T10:30:00Z"
distro: "Ubuntu"
distro_version: "24.04"
package_manager: "apt"
package_count: 142
packages:
  - vim
  - git
  - docker.io
  - nodejs
  # ... more packages
has_bashrc: true
```

### bashrc

Your raw `~/.bashrc` content (if backed up).

## Custom Server API

If using `--server`, your server should implement these endpoints:

### POST /api/backup

```json
{
  "metadata": { /* tuxsync.yaml content */ },
  "bashrc": "# .bashrc content..."
}
```
Response: `{"backup_id": "unique-id"}`

### GET /api/backup/{backup_id}

Response:

```json
{
  "metadata": { /* tuxsync.yaml content */ },
  "bashrc": "# .bashrc content..."
}
```

## Development & Testing

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

GPL-3.0 License - See [LICENSE](LICENSE) for details.

## Credits

- Package restoration powered by [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli)
- Web interface: [tuxmate](https://github.com/abusoww/tuxmate) by [@abusoww](https://github.com/abusoww)
