# TuxSync

**Profile Sync for Linux Users** - Like Apple's Migration Assistant or Chrome Sync, but for your Linux packages and configurations.

## Features

- **Multi-Distro Support**: Works on Ubuntu/Debian (apt), Fedora (dnf), and Arch (pacman)
- **Privacy First**: Choose between GitHub Gists (convenient) or your own custom server (private)
- **Loose Coupling**: Uses [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) as an external executor - no embedded code
- **Smart Scanning**: Only backs up user-installed packages, filters out libraries
- **Magic Restore**: One-liner command to restore your setup on any Linux machine

## Quick Start

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/Gururagavendra/tuxsync.git
cd tuxsync

# Install with uv (recommended)
uv sync

# Or use the wrapper script
chmod +x tuxsync.sh
./tuxsync.sh help
\`\`\`

### Create a Backup

\`\`\`bash
# Interactive mode (recommended)
./tuxsync.sh backup

# Or using uv
uv run tuxsync backup

# Skip bashrc backup
uv run tuxsync backup --no-bashrc

# Direct to GitHub (non-interactive)
uv run tuxsync backup --github --non-interactive
\`\`\`

### Restore on New Machine

\`\`\`bash
# Using the magic command (shown after backup)
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>

# Or install TuxSync and restore
uv run tuxsync restore <GIST_ID>

# Dry run to see what would happen
uv run tuxsync restore <GIST_ID> --dry-run

# Skip package installation, only restore bashrc
uv run tuxsync restore <GIST_ID> --skip-packages
\`\`\`

### List Your Backups

\`\`\`bash
uv run tuxsync list
\`\`\`

## Requirements

- **Python 3.10+**
- **GitHub CLI (gh)** - For GitHub Gist storage: https://cli.github.com/
- **gum** (optional) - For pretty terminal menus: https://github.com/charmbracelet/gum
- **tuxmate-cli** - For cross-distro package installation: https://github.com/Gururagavendra/tuxmate-cli

The wrapper script (\`tuxsync.sh\`) will help install these if missing.

## Architecture

TuxSync follows a **loose coupling** principle:

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                       TuxSync                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Scanner  │  │ Storage  │  │ Restore  │              │
│  │ (Brain)  │  │ Backend  │  │ Manager  │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                      │
│       ▼             ▼             ▼                      │
│  [apt/dnf/     [GitHub/      [tuxmate-cli]               │
│   pacman]      Custom]        Executor                   │
└─────────────────────────────────────────────────────────┘
\`\`\`

- **TuxSync** = The Brain (orchestrates everything)
- **tuxmate-cli** = The Hands (does the actual package installation)
- If tuxmate-cli isn't installed, TuxSync will fail gracefully with installation instructions

## Configuration

TuxSync creates backups with two files:

### \`tuxsync.yaml\`
\`\`\`yaml
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
\`\`\`

### \`bashrc\`
Your raw \`~/.bashrc\` content (if backed up).

## Custom Server API

If using \`--server\`, your server should implement:

### POST \`/api/backup\`
\`\`\`json
{
  "metadata": { /* tuxsync.yaml content */ },
  "bashrc": "# .bashrc content..."
}
\`\`\`
Response: \`{"backup_id": "unique-id"}\`

### GET \`/api/backup/{backup_id}\`
Response:
\`\`\`json
{
  "metadata": { /* tuxsync.yaml content */ },
  "bashrc": "# .bashrc content..."
}
\`\`\`

## Development

\`\`\`bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
\`\`\`

## License

MIT License - See [LICENSE](LICENSE) for details.

## Related Projects

- [tuxmate-cli](https://github.com/Gururagavendra/tuxmate-cli) - Cross-distro package installer CLI (used as executor)
