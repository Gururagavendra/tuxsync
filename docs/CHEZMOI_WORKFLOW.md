# Chezmoi Integration - Behind the Scenes

This document explains exactly what happens when you use TuxSync with `--use-chezmoi` and `--chezmoi-repo` options.

## Table of Contents
- [Overview](#overview)
- [Backup Workflow](#backup-workflow)
- [Restore Workflow](#restore-workflow)
- [Commands Reference](#commands-reference)
- [File Structure](#file-structure)

---

## Overview

When you use `--use-chezmoi`, TuxSync delegates comprehensive dotfile management to [chezmoi](https://github.com/twpayne/chezmoi), a popular dotfile manager. This means **all your configuration files** are backed up and versioned in a GitHub repository, not just in a Gist.

### What Gets Managed by Chezmoi?
- `~/.bashrc`, `~/.zshrc`, `~/.vimrc`, `~/.gitconfig`
- Entire `~/.config/` directory (nvim, i3, kitty, tmux, etc.)
- `~/.ssh/config` (optional, you control what to add)
- Any other dotfiles you add
- Templates with variables (e.g., different configs per machine)
- Encrypted secrets (optional, using age encryption)

---

## Backup Workflow

### Command
```bash
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles
```

### What Happens Step-by-Step

#### Step 1: Check if chezmoi is installed
```bash
# TuxSync runs internally:
which chezmoi
```

**If not found**, TuxSync automatically installs it:
```bash
# Installation command executed:
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
```

This downloads and installs chezmoi to `~/.local/bin/chezmoi`.

---

#### Step 2: Initialize chezmoi with your repository
```bash
# Command executed by TuxSync:
chezmoi init username/dotfiles
```

**What this does:**
- Creates `~/.local/share/chezmoi/` directory (the "source" directory)
- Clones your GitHub repository `https://github.com/username/dotfiles` into this directory
- If the repo doesn't exist yet, chezmoi creates a new Git repository locally

**Behind the scenes:**
```bash
git clone https://github.com/username/dotfiles.git ~/.local/share/chezmoi
```

---

#### Step 3: Chezmoi automatically discovers dotfiles
Chezmoi scans your home directory for common configuration files and adds them. You can also manually add files:

```bash
# If you want to add specific files (manual step):
chezmoi add ~/.bashrc
chezmoi add ~/.zshrc
chezmoi add ~/.config/nvim
```

**What chezmoi does internally:**
- Copies `~/.bashrc` → `~/.local/share/chezmoi/dot_bashrc`
- Copies `~/.config/nvim/` → `~/.local/share/chezmoi/dot_config/nvim/`
- The `dot_` prefix tells chezmoi to convert it back to `.bashrc` when applying

---

#### Step 4: Commit and push changes
```bash
# Commands executed by TuxSync:
cd ~/.local/share/chezmoi
git add .
git status --porcelain  # Check if there are changes

# If there are changes:
git commit -m "Update dotfiles via tuxsync"
git push
```

**Output you'll see:**
```
✓ chezmoi installed successfully
🔧 Initializing chezmoi with username/dotfiles
✓ chezmoi initialized
📤 Pushing dotfiles to remote repository...
✓ Dotfiles pushed successfully
```

---

#### Step 5: Package backup continues as normal
TuxSync then proceeds to back up your package list to a GitHub Gist (separate from chezmoi).

**Final result:**
- **GitHub Gist** → Contains package list and basic .bashrc
- **GitHub Repo** (`username/dotfiles`) → Contains ALL your dotfiles, managed by chezmoi

---

## Restore Workflow

### Command
```bash
tuxsync restore <GIST_ID> --use-chezmoi --chezmoi-repo username/dotfiles
```

### What Happens Step-by-Step

#### Step 1: Restore packages first
TuxSync restores your packages using the standard workflow (fetches from Gist, installs via tuxmate-cli).

---

#### Step 2: Check if chezmoi is installed
```bash
# TuxSync runs internally:
which chezmoi
```

**If not found**, TuxSync automatically installs it (same as backup):
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
```

---

#### Step 3: Initialize chezmoi with your dotfiles repository
```bash
# Command executed by TuxSync:
chezmoi init username/dotfiles
```

**What this does:**
- Clones your dotfiles repository from GitHub
- Places it in `~/.local/share/chezmoi/`

**Behind the scenes:**
```bash
git clone https://github.com/username/dotfiles.git ~/.local/share/chezmoi
```

---

#### Step 4: Apply dotfiles to your system
```bash
# Command executed by TuxSync:
chezmoi apply
```

**What this does:**
- Reads all files from `~/.local/share/chezmoi/`
- Converts filenames back (e.g., `dot_bashrc` → `.bashrc`)
- Copies them to your home directory
- Overwrites existing files (backs up originals if configured)

**Example file transformations:**
```
~/.local/share/chezmoi/dot_bashrc
  → ~/.bashrc

~/.local/share/chezmoi/dot_config/nvim/init.vim
  → ~/.config/nvim/init.vim

~/.local/share/chezmoi/dot_gitconfig
  → ~/.gitconfig
```

---

#### Step 5: Done!
Your entire system is now restored with:
- ✅ All packages installed
- ✅ All dotfiles applied
- ✅ Your environment is identical to the backup source

**Output you'll see:**
```
✓ Packages installed successfully
📁 Restoring dotfiles with chezmoi...
✓ chezmoi installed successfully
🔧 Initializing chezmoi with username/dotfiles
✓ chezmoi initialized
📝 Applying dotfiles...
✓ Dotfiles applied
✓ Dotfiles restored successfully
```

---

## Commands Reference

### Manual chezmoi Commands (if you want to use it directly)

```bash
# Initialize chezmoi with a GitHub repo
chezmoi init username/dotfiles

# Add a file to chezmoi management
chezmoi add ~/.vimrc

# See what changes would be applied
chezmoi diff

# Apply dotfiles (dry run)
chezmoi apply --dry-run

# Apply dotfiles (actual)
chezmoi apply

# Update dotfiles from remote repo
chezmoi update

# Edit a file managed by chezmoi
chezmoi edit ~/.bashrc

# View the chezmoi source directory
chezmoi source-path
# Output: /home/user/.local/share/chezmoi

# Push changes to GitHub
cd $(chezmoi source-path)
git add .
git commit -m "Update configs"
git push
```

---

## File Structure

### On Your System

```
$HOME/
├── .bashrc                    # Your actual dotfile
├── .zshrc
├── .vimrc
├── .gitconfig
└── .config/
    ├── nvim/
    ├── i3/
    └── kitty/

$HOME/.local/share/chezmoi/    # Chezmoi source directory (Git repo)
├── .git/                       # Git repository
├── dot_bashrc                  # Maps to ~/.bashrc
├── dot_zshrc                   # Maps to ~/.zshrc
├── dot_vimrc                   # Maps to ~/.vimrc
├── dot_gitconfig               # Maps to ~/.gitconfig
└── dot_config/                 # Maps to ~/.config/
    ├── nvim/
    ├── i3/
    └── kitty/
```

### On GitHub

**Repository: `username/dotfiles`**
```
dotfiles/
├── README.md
├── dot_bashrc
├── dot_zshrc
├── dot_gitconfig
└── dot_config/
    ├── nvim/
    ├── i3/
    └── kitty/
```

---

## Why This Architecture?

### Separation of Concerns
- **GitHub Gist** → Quick package list + basic bashrc (lightweight, fast)
- **GitHub Repo** → Comprehensive dotfile management (version control, history)

### Benefits
1. **Version Control** - Your dotfiles have full Git history
2. **Portability** - Works across any Linux distro
3. **Privacy** - Everything stays in YOUR GitHub account
4. **Flexibility** - Use chezmoi's advanced features (templates, encryption)
5. **Independence** - chezmoi and TuxSync work separately, loose coupling

### Example: Machine-Specific Configs

Chezmoi supports templates, so you can have different configs per machine:

```bash
# In dot_bashrc.tmpl
export EDITOR={{ if eq .chezmoi.hostname "work-laptop" }}vim{{ else }}nano{{ end }}
```

This automatically adapts based on the hostname!

---

## Troubleshooting

### View what chezmoi would do (dry run)
```bash
chezmoi apply --dry-run --verbose
```

### Check chezmoi status
```bash
chezmoi status
```

### Verify files are managed
```bash
chezmoi managed
```

### Update from remote and apply
```bash
chezmoi update
```

### View differences between source and target
```bash
chezmoi diff
```

---

## Security Notes

### Sensitive Files
Be careful with sensitive files like `~/.ssh/id_rsa`. Chezmoi supports encryption:

```bash
# Install age encryption tool
sudo apt install age  # Ubuntu/Debian
brew install age      # macOS

# Generate encryption key
age-keygen -o ~/.config/chezmoi/key.txt

# Add encrypted file
chezmoi add --encrypt ~/.ssh/id_rsa
```

### Private Repository
Make sure your dotfiles repository is **private** if it contains sensitive information:

```bash
# On GitHub, set repository visibility to Private
```

---

## Learn More

- [Official chezmoi docs](https://www.chezmoi.io/)
- [chezmoi GitHub](https://github.com/twpayne/chezmoi)
- [TuxSync Architecture](ARCHITECTURE.md)

---

## Quick Reference

| Action | Command |
|--------|---------|
| Backup with chezmoi | `tuxsync backup --use-chezmoi --chezmoi-repo user/dotfiles` |
| Restore with chezmoi | `tuxsync restore <ID> --use-chezmoi --chezmoi-repo user/dotfiles` |
| View chezmoi files | `chezmoi managed` |
| Update dotfiles | `chezmoi update` |
| Edit managed file | `chezmoi edit ~/.bashrc` |
| Dry run apply | `chezmoi apply --dry-run` |
