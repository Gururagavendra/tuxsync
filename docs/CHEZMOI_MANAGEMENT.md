# Managing Dotfiles with Chezmoi

This guide explains how to manage your dotfiles using chezmoi with TuxSync, including what files are backed up by default, how to add new files, and how to handle sensitive data.

## Table of Contents
- [Understanding the Defaults](#understanding-the-defaults)
- [Adding Files to Chezmoi](#adding-files-to-chezmoi)
- [Adding Sensitive Files (Encrypted)](#adding-sensitive-files-encrypted)
- [Configuring Exclusions](#configuring-exclusions)
- [Common Workflows](#common-workflows)
- [Quick Reference](#quick-reference)
- [Troubleshooting](#troubleshooting)

---

## Understanding the Defaults

### What TuxSync Backs Up Automatically

When you run `tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles`:

**TuxSync handles:**
- ✅ Package list → Stored in GitHub Gist
- ✅ `~/.bashrc` → Stored in GitHub Gist

**Chezmoi handles:**
- ⚠️ **Nothing by default** - You must explicitly add files

### Important: Chezmoi is Opt-In

**Chezmoi does NOT automatically scan or add files.** This is a safety feature to prevent accidentally backing up:
- Sensitive credentials (SSH keys, API tokens)
- Large cache files
- Temporary data
- Private information

You have **full control** over what gets backed up.

---

## Adding Files to Chezmoi

### Basic File Management

#### Add Individual Files

```bash
# Add configuration files
chezmoi add ~/.vimrc
chezmoi add ~/.gitconfig
chezmoi add ~/.zshrc
chezmoi add ~/.tmux.conf

# Add shell configurations
chezmoi add ~/.bashrc
chezmoi add ~/.bash_profile
chezmoi add ~/.profile
```

#### Add Entire Directories

```bash
# Add entire config directories
chezmoi add ~/.config/nvim
chezmoi add ~/.config/i3
chezmoi add ~/.config/kitty
chezmoi add ~/.config/tmux
chezmoi add ~/.config/alacritty
```

#### View Managed Files

```bash
# See all files managed by chezmoi
chezmoi managed

# Example output:
# .bashrc
# .gitconfig
# .vimrc
# .config/nvim/init.vim
# .config/i3/config
```

### Recommended Files to Add

#### Essential Developer Files
```bash
chezmoi add ~/.gitconfig
chezmoi add ~/.vimrc
chezmoi add ~/.bashrc
chezmoi add ~/.zshrc
```

#### Editor Configurations
```bash
chezmoi add ~/.config/nvim     # Neovim
chezmoi add ~/.config/code     # VS Code (be selective!)
chezmoi add ~/.vimrc           # Vim
chezmoi add ~/.emacs.d         # Emacs
```

#### Terminal & Shell
```bash
chezmoi add ~/.config/alacritty
chezmoi add ~/.config/kitty
chezmoi add ~/.tmux.conf
chezmoi add ~/.config/fish
```

#### Window Managers
```bash
chezmoi add ~/.config/i3
chezmoi add ~/.config/sway
chezmoi add ~/.config/hypr
```

#### Development Tools
```bash
chezmoi add ~/.config/gh       # GitHub CLI (safe, no tokens)
chezmoi add ~/.npmrc           # (check for tokens first!)
chezmoi add ~/.cargo/config    # Rust
chezmoi add ~/.pypirc          # Python (no passwords!)
```

### Pushing Changes

After adding files, push to your repository:

```bash
cd ~/.local/share/chezmoi
git add .
git commit -m "Add dotfiles configuration"
git push
```

Or use chezmoi's built-in git commands:

```bash
chezmoi git add .
chezmoi git commit -- -m "Add dotfiles"
chezmoi git push
```

---

## Adding Sensitive Files (Encrypted)

### ⚠️ CRITICAL WARNING

**NEVER add sensitive files without encryption!**

Sensitive files include:
- SSH private keys (`~/.ssh/id_*`)
- Docker credentials (`~/.docker/config.json`)
- Cloud provider credentials (`~/.aws/`, `~/.config/gcloud/`)
- Kubernetes configs (`~/.kube/config`)
- API tokens, passwords, certificates

### Setting Up Encryption

#### One-Time Setup

```bash
# Install age encryption tool
# Ubuntu/Debian
sudo apt install age

# Fedora
sudo dnf install age

# Arch
sudo pacman -S age

# macOS
brew install age
```

#### Generate Encryption Key

```bash
# Generate age key
age-keygen -o ~/.config/chezmoi/key.txt

# Example output:
# Public key: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
# ⚠️ IMPORTANT: Save this key securely!
```

#### Backup Your Encryption Key

**Critical:** Without this key, you cannot decrypt your secrets!

Store it in:
- Password manager (recommended)
- Encrypted USB drive
- Secure cloud storage (encrypted)
- Physical safe (paper backup)

### Adding Encrypted Files

```bash
# SSH keys
chezmoi add --encrypt ~/.ssh/id_rsa
chezmoi add --encrypt ~/.ssh/id_ed25519
chezmoi add --encrypt ~/.ssh/config  # if contains sensitive info

# Docker credentials
chezmoi add --encrypt ~/.docker/config.json

# Cloud provider credentials
chezmoi add --encrypt ~/.aws/credentials
chezmoi add --encrypt ~/.aws/config
chezmoi add --encrypt ~/.config/gcloud/credentials.db
chezmoi add --encrypt ~/.azure/azureProfile.json

# Kubernetes
chezmoi add --encrypt ~/.kube/config

# Other sensitive files
chezmoi add --encrypt ~/.netrc
chezmoi add --encrypt ~/.npmrc  # if contains auth tokens
```

### Verify Encryption

Check that files are actually encrypted:

```bash
# Check chezmoi source directory
cd ~/.local/share/chezmoi
ls -la

# Encrypted files will have .age extension:
# encrypted_private_id_rsa.age         ✓ Encrypted
# encrypted_private_config.json.age    ✓ Encrypted

# Plain files (no .age):
# private_id_rsa                       ✗ NOT ENCRYPTED - DANGER!
```

### Pushing Encrypted Files

```bash
# Push encrypted files safely
cd ~/.local/share/chezmoi
git add .
git commit -m "Add encrypted credentials"
git push

# Your secrets are now safely stored encrypted on GitHub
```

---

## Configuring Exclusions

### Using .chezmoiignore

Create `~/.config/chezmoi/chezmoiignore` to exclude files and directories:

```bash
# Edit ignore file
chezmoi edit-config
```

Or create it manually:

```bash
# ~/.config/chezmoi/chezmoiignore

# Cache directories
.cache/
.local/share/
.npm/_cacache/
.cargo/registry/

# Browser data (large and sensitive)
.mozilla/firefox/*/cache2/
.mozilla/firefox/*/thumbnails/
.mozilla/firefox/*/sessionstore*
.config/google-chrome/*/Cache/
.config/google-chrome/*/Service Worker/
.config/google-chrome/*/History

# Shell history (may contain passwords)
.bash_history
.zsh_history
.python_history

# Temporary files
*.swp
*.swo
*~
.DS_Store

# Build artifacts
node_modules/
venv/
__pycache__/
target/
dist/
build/

# Logs
*.log
```

### Selective Directory Backup

Instead of backing up entire `.config/`, be selective:

```bash
# Good: Only backup what you need
chezmoi add ~/.config/nvim
chezmoi add ~/.config/i3
chezmoi add ~/.config/kitty

# Avoid: Entire .config (contains cache, logs, etc.)
# chezmoi add ~/.config  # Don't do this!
```

---

## Common Workflows

### Initial Dotfiles Setup

```bash
# 1. Backup with TuxSync
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles

# 2. Add your essential dotfiles
chezmoi add ~/.vimrc
chezmoi add ~/.gitconfig
chezmoi add ~/.bashrc
chezmoi add ~/.config/nvim

# 3. Setup encryption for secrets
sudo apt install age
age-keygen -o ~/.config/chezmoi/key.txt

# 4. Add encrypted secrets
chezmoi add --encrypt ~/.ssh/id_rsa
chezmoi add --encrypt ~/.docker/config.json

# 5. Push everything
cd ~/.local/share/chezmoi
git push
```

### Adding a New Configuration File

```bash
# Edit/create your config file normally
vim ~/.config/mynewapp/config.yml

# Add to chezmoi when ready
chezmoi add ~/.config/mynewapp/config.yml

# Push to repository
cd ~/.local/share/chezmoi
git push
```

### Editing Managed Files

```bash
# Option 1: Edit with chezmoi (recommended)
chezmoi edit ~/.vimrc

# This opens in your editor, changes are tracked

# Option 2: Edit directly and re-add
vim ~/.vimrc
chezmoi add ~/.vimrc
```

### Removing Files from Chezmoi

```bash
# Remove file from chezmoi management
chezmoi forget ~/.vimrc

# The file stays on your system, just not managed by chezmoi
```

### Syncing Changes from Multiple Machines

```bash
# On machine A: Make changes and push
chezmoi edit ~/.bashrc
cd ~/.local/share/chezmoi && git push

# On machine B: Pull and apply changes
chezmoi update
# This pulls latest changes and applies them
```

---

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Add a file | `chezmoi add ~/.vimrc` |
| Add file (encrypted) | `chezmoi add --encrypt ~/.ssh/id_rsa` |
| Add entire directory | `chezmoi add ~/.config/nvim` |
| View managed files | `chezmoi managed` |
| Edit managed file | `chezmoi edit ~/.vimrc` |
| Remove from chezmoi | `chezmoi forget ~/.vimrc` |
| Check differences | `chezmoi diff` |
| Apply changes | `chezmoi apply` |
| Update from remote | `chezmoi update` |
| View source directory | `chezmoi source-path` |

### File Locations

| Item | Path |
|------|------|
| Chezmoi source directory | `~/.local/share/chezmoi/` |
| Chezmoi config | `~/.config/chezmoi/chezmoi.toml` |
| Age encryption key | `~/.config/chezmoi/key.txt` |
| Ignore file | `~/.config/chezmoi/chezmoiignore` |

### Git Operations

```bash
# Inside chezmoi source directory
cd ~/.local/share/chezmoi

# Standard git commands work:
git status
git add .
git commit -m "Update configs"
git push
git pull

# Or use chezmoi's git integration:
chezmoi git status
chezmoi git add .
chezmoi git commit -- -m "Update"
chezmoi git push
```

---

## Troubleshooting

### Files Not Showing Up in Repository

**Problem:** Added files but they're not in the GitHub repo.

**Solution:**
```bash
cd ~/.local/share/chezmoi
git status  # Check what's staged
git add .
git commit -m "Add missing files"
git push
```

### Encryption Not Working

**Problem:** Files added with `--encrypt` but not encrypted.

**Check:**
```bash
# Verify age is installed
age --version

# Verify key exists
ls -la ~/.config/chezmoi/key.txt

# Check file is actually encrypted
cd ~/.local/share/chezmoi
ls -la *.age  # Should see .age files
```

### "Key Not Found" Error on Restore

**Problem:** Can't decrypt files on new machine.

**Solution:**
```bash
# Copy your age key from backup
# (from password manager or secure storage)
mkdir -p ~/.config/chezmoi
echo "YOUR_PRIVATE_KEY" > ~/.config/chezmoi/key.txt
chmod 600 ~/.config/chezmoi/key.txt

# Then apply
chezmoi apply
```

### Files Have Wrong Permissions

**Problem:** SSH keys have wrong permissions after restore.

**Solution:**
```bash
# Fix SSH permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 600 ~/.ssh/config
```

### Accidentally Committed Sensitive File Unencrypted

**URGENT:** If you committed a sensitive file without encryption:

```bash
# 1. Immediately rotate the credential
# (Generate new SSH key, API token, etc.)

# 2. Remove from Git history
cd ~/.local/share/chezmoi
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push
git push origin --force --all

# 4. Re-add with encryption
chezmoi add --encrypt ~/.ssh/id_rsa
git push
```

### Repository Too Large

**Problem:** Dotfiles repository is huge.

**Solution:**
```bash
# Check what's taking space
cd ~/.local/share/chezmoi
du -sh *

# Common culprits:
# - Browser profiles (cache, history)
# - Node modules
# - Build artifacts

# Add to .chezmoiignore:
# .mozilla/firefox/*/cache2/
# .config/google-chrome/*/Cache/
# node_modules/
```

---

## Advanced Features

### Templates

Chezmoi supports templates for machine-specific configs:

```bash
# Create a template file
chezmoi add --template ~/.gitconfig

# Edit to use variables
chezmoi edit ~/.gitconfig

# Example template:
[user]
    name = "Your Name"
    {{ if eq .chezmoi.hostname "work-laptop" }}
    email = "work@company.com"
    {{ else }}
    email = "personal@email.com"
    {{ end }}
```

### Multiple Machines

```bash
# Different config per machine
chezmoi add --template ~/.bashrc

# In the template:
{{ if eq .chezmoi.hostname "desktop" }}
export DISPLAY=:0
{{ end }}
```

### Scripts

Run scripts during apply:

```bash
# Create script: run_once_install-tools.sh
cd ~/.local/share/chezmoi
vim run_once_install-tools.sh

#!/bin/bash
# This runs once to install tools
sudo apt install -y vim git curl
```

---

## Best Practices

### 1. Start Small
- Begin with essential files (`.gitconfig`, `.vimrc`, `.bashrc`)
- Add more as needed
- Don't backup everything at once

### 2. Use Encryption for Anything Sensitive
- When in doubt, encrypt
- It's better to over-encrypt than under-encrypt

### 3. Keep Repository Private
- Always use private GitHub repository
- Even with encryption, keep it private

### 4. Regular Backups of Encryption Key
- Store age key in multiple secure locations
- Test recovery before you need it

### 5. Review Before Pushing
```bash
cd ~/.local/share/chezmoi
git diff  # Review what changed
git log   # Review history
```

### 6. Test Restore Periodically
```bash
# On a test VM or container
tuxsync restore <GIST_ID> --use-chezmoi --chezmoi-repo user/dotfiles --dry-run
```

---

## Additional Resources

- [TuxSync Chezmoi Workflow](CHEZMOI_WORKFLOW.md) - Behind-the-scenes commands
- [Security Credentials Guide](SECURITY_CREDENTIALS.md) - Detailed security best practices
- [Official Chezmoi Documentation](https://www.chezmoi.io/)
- [Age Encryption](https://age-encryption.org/)
- [TuxSync Architecture](ARCHITECTURE.md)

---

## Questions?

- [TuxSync GitHub Issues](https://github.com/Gururagavendra/tuxsync/issues)
- [TuxSync Discussions](https://github.com/Gururagavendra/tuxsync/discussions)
- [Chezmoi GitHub](https://github.com/twpayne/chezmoi)
