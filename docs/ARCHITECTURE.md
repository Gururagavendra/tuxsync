# Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     TUXSYNC ARCHITECTURE                         │
└──────────────────────────────────────────────────────────────────┘

                         User Command
                      tuxsync [command]
                              ↓
                ┌─────────────────────────────┐
                │     CLI Interface           │
                │       (cli.py)              │
                │                             │
                │  • backup    • restore      │
                │  • list      • config       │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │    Scanner Module           │
                │     (scanner.py)            │
                │                             │
                │  • Detect distro            │
                │  • Query package manager    │
                │    - apt-mark (Ubuntu)      │
                │    - dnf history (Fedora)   │
                │    - pacman -Qe (Arch)      │
                │  • Filter system packages   │
                │  • Scan bashrc/configs      │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │   Storage Backend           │
                │     (storage.py)            │
                │                             │
                │  • GitHub Gists (default)   │
                │  • Custom server (future)   │
                │  • Save/retrieve profiles   │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │   Restore Manager           │
                │     (restore.py)            │
                │                             │
                │  • Fetch profile            │
                │  • Delegate to tuxmate-cli  │
                │  • Restore bashrc/configs   │
                │  • Dry-run mode             │
                └──────────────┬──────────────┘
                               ↓
                  ┌────────────────────────┐
                  │  tuxmate-cli           │
                  │  (external executor)   │
                  │                        │
                  │  Cross-distro install  │
                  │  Uses tuxmate's DB     │
                  └────────────┬───────────┘
                               ↓
                       📦 Restored System

Note: tuxmate-cli uses the curated package database from
      tuxmate (https://github.com/abusoww/tuxmate)
```

## Data Flow

### Backup Flow

```
User → tuxsync backup → Scanner → Storage → GitHub Gist
                           ↓
                    Package List + Configs
```

1. **Scanner** queries package manager (apt/dnf/pacman)
2. Filters system packages (libraries, dependencies)
3. Collects bashrc and config files
4. **Storage** saves to GitHub Gist with metadata

### Restore Flow

```
User → tuxsync restore <GIST_ID> → Storage → Restore Manager → tuxmate-cli → System
                                       ↓
                               Profile Data (YAML)
```

1. **Storage** fetches profile from GitHub Gist
2. **Restore Manager** parses package list
3. Calls `tuxmate-cli install <packages>` via subprocess
4. Restores bashrc and configs to home directory

## Key Components

- **Scanner**: Distro-agnostic package detection
- **Storage**: Pluggable backend (GitHub Gists, custom server)
- **Restore Manager**: Orchestrates restoration workflow
- **Utils**: Helper functions (distro detection, subprocess execution)

## Backup Structure

TuxSync stores backups with two files in a GitHub Gist:

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

Raw content of `~/.bashrc` (if backed up).

## Storage Backend

### GitHub Gists (Current)

- **Pros**: Free, no server setup, public/private options
- **Cons**: Requires GitHub CLI (gh), tied to GitHub ecosystem
- **Format**: YAML with metadata (distro, packages, configs)

### Custom Server

- **Pros**: Complete privacy, self-hosted
- **Cons**: Requires server setup
- **Implementation**: Simple REST API for upload/download
- **Status**: WIP - See [Custom Server API](CUSTOM_SERVER.md) for details

## Magic Restore Command

TuxSync generates a one-liner for new machines:

```bash
curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>
```

This script:
1. Installs Python + uv (if needed)
2. Installs tuxmate-cli (if needed)
3. Installs TuxSync
4. Runs `tuxsync restore <GIST_ID>`

## Design Philosophy

### Loose Coupling

TuxSync follows a **separation of concerns** principle:

- **TuxSync** = The Brain (orchestrates backup/restore workflow)
- **tuxmate-cli** = The Hands (handles cross-distro package installation using [tuxmate's](https://github.com/abusoww/tuxmate) curated package database)

This design means:
- TuxSync calls `tuxmate-cli` as a subprocess (no code sharing)
- If tuxmate-cli isn't installed, TuxSync auto-downloads it gracefully
- Updates to either tool don't break the other
- Users can use tuxmate-cli independently for package installation

### Why This Architecture?

1. **Single Responsibility**: Each tool does one thing well
2. **Independent Updates**: tuxmate-cli can improve without TuxSync changes
3. **User Choice**: Users can use tuxmate-cli directly if they prefer
4. **Smaller Codebase**: No duplicate package installation logic
5. **Better Maintenance**: Bugs in one tool don't affect the other


## Quick Links

- [README](../README.md) - User guide with examples
