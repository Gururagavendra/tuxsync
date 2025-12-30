# Backing Up Sensitive Credentials

This guide explains how to safely backup and restore sensitive data like SSH keys, Docker credentials, cloud provider tokens, and browser profiles using TuxSync with chezmoi encryption.

## Table of Contents
- [Overview](#overview)
- [What Can Be Backed Up](#what-can-be-backed-up)
- [Security Considerations](#security-considerations)
- [How It Works](#how-it-works)
- [Step-by-Step Guide](#step-by-step-guide)
- [Best Practices](#best-practices)
- [Enterprise Considerations](#enterprise-considerations)
- [Troubleshooting](#troubleshooting)

---

## Overview

TuxSync integrates with [chezmoi](https://www.chezmoi.io/), which provides **encrypted storage** for sensitive files using [age](https://age-encryption.org/) or GPG encryption. This means you can backup:
- SSH private keys
- Docker/container registry credentials
- Cloud provider credentials (AWS, GCP, Azure)
- Kubernetes configs
- API tokens and secrets
- Browser profiles (with caution)

**Important:** All sensitive data is encrypted **before** being pushed to your dotfiles repository. Your secrets never leave your machine in plain text.

---

## What Can Be Backed Up

### ✅ Recommended (Low-Medium Risk)

| Item | Location | Risk Level | Notes |
|------|----------|-----------|-------|
| **SSH Keys** | `~/.ssh/id_*` | 🟡 Medium | Encrypt required, use passphrase |
| **Git Config** | `~/.gitconfig` | 🟢 Low | Usually safe (email/name) |
| **Docker Config** | `~/.docker/config.json` | 🟡 Medium | Contains registry credentials |
| **AWS Credentials** | `~/.aws/credentials` | 🔴 High | Encrypt + rotate on restore |
| **Kubernetes Config** | `~/.kube/config` | 🔴 High | Contains cluster access tokens |
| **GCP Credentials** | `~/.config/gcloud/` | 🔴 High | Service account keys |
| **Azure Config** | `~/.azure/` | 🔴 High | Subscription credentials |

### ⚠️ Use with Caution

| Item | Location | Risk Level | Notes |
|------|----------|-----------|-------|
| **Browser Profiles** | `~/.mozilla/firefox/`, `~/.config/google-chrome/` | 🟡 Medium | Contains cookies, saved passwords |
| **Shell History** | `~/.bash_history`, `~/.zsh_history` | 🟡 Medium | May contain passwords in commands |
| **Network Config** | `~/.netrc` | 🔴 High | Plain text passwords |

### ❌ NOT Recommended

| Item | Why Not | Alternative |
|------|---------|-------------|
| **Browser Passwords** | Use password manager instead | Bitwarden, 1Password, LastPass |
| **Company VPN Credentials** | May violate security policy | Manual setup with company IT |
| **Session Tokens** | Expire quickly anyway | Re-authenticate after restore |
| **Database Passwords** | Security risk if leaked | Environment variables, vaults |

---

## Security Considerations

### Encryption Methods

Chezmoi supports two encryption methods:

#### 1. **Age Encryption** (Recommended)
- Modern, simple encryption tool
- Fast and secure
- Easy to use

#### 2. **GPG Encryption**
- More established, widely used
- Requires GPG setup
- More complex key management

### Risk Assessment

Before backing up sensitive data, consider:

1. **Where is the backup stored?**
   - Private GitHub repo: Medium risk
   - Public GitHub repo: ⚠️ **NEVER** do this
   - Self-hosted server: Low risk

2. **Who has access?**
   - Only you: Low risk
   - Team members: Medium risk (use GPG with multiple recipients)
   - Public: ⚠️ **NEVER**

3. **What if the backup is compromised?**
   - Encrypted with strong passphrase: Safe
   - Encrypted with weak passphrase: Risk of brute force
   - Not encrypted: ⚠️ **CRITICAL RISK**

---

## How It Works

### Encryption Flow

```
Your Machine                    GitHub Repository
─────────────                   ─────────────────

~/.ssh/id_rsa  
    ↓
[Encrypt with age/GPG]
    ↓
encrypted_id_rsa.age            → Push → encrypted_id_rsa.age
    ↓                                           ↓
[Store in chezmoi repo]                    [Safe in Git]
    ↓
~/.local/share/chezmoi/
```

### Restore Flow

```
GitHub Repository               New Machine
─────────────────              ────────────

encrypted_id_rsa.age   → Pull →   [Chezmoi repo]
                                        ↓
                            [Decrypt with passphrase]
                                        ↓
                                  ~/.ssh/id_rsa
```

### Key Points

- 🔐 **Encrypted before leaving your machine**
- 🔑 **Only you have the decryption key**
- 📦 **Stored safely in your Git repository**
- 🚀 **Automatically restored on new machines**

---

## Step-by-Step Guide

### Prerequisites

1. **Install age** (for encryption):
   ```bash
   # Ubuntu/Debian
   sudo apt install age

   # Fedora
   sudo dnf install age

   # Arch
   sudo pacman -S age

   # macOS
   brew install age
   ```

2. **Configure chezmoi for encryption**:
   ```bash
   # Generate age key
   age-keygen -o ~/.config/chezmoi/key.txt

   # Important: Backup this key securely!
   # Without it, you can't decrypt your secrets
   ```

### Backup with Encrypted Secrets

#### Step 1: Initial Backup
```bash
# Start normal backup with chezmoi
tuxsync backup --use-chezmoi --chezmoi-repo username/dotfiles
```

#### Step 2: Add Encrypted Files
```bash
# Add SSH keys (encrypted)
chezmoi add --encrypt ~/.ssh/id_rsa
chezmoi add --encrypt ~/.ssh/id_ed25519

# Add Docker credentials (encrypted)
chezmoi add --encrypt ~/.docker/config.json

# Add AWS credentials (encrypted)
chezmoi add --encrypt ~/.aws/credentials
chezmoi add --encrypt ~/.aws/config

# Add Kubernetes config (encrypted)
chezmoi add --encrypt ~/.kube/config
```

#### Step 3: Verify Encryption
```bash
# Check that files are encrypted in chezmoi repo
cd ~/.local/share/chezmoi
ls -la

# You should see .age files (encrypted):
# encrypted_private_id_rsa.age
# encrypted_private_config.json.age
```

#### Step 4: Push to Repository
```bash
# Chezmoi automatically commits and pushes
cd ~/.local/share/chezmoi
git add .
git commit -m "Add encrypted credentials"
git push
```

### Restore with Encrypted Secrets

#### Step 1: Restore System
```bash
# Normal restore process
tuxsync restore <GIST_ID> --use-chezmoi --chezmoi-repo username/dotfiles
```

#### Step 2: Decrypt Secrets
```bash
# Chezmoi will prompt for decryption key
# Make sure your age key is available at ~/.config/chezmoi/key.txt

# Apply all dotfiles (including encrypted ones)
chezmoi apply
```

#### Step 3: Verify Restoration
```bash
# Check that SSH keys are restored
ls -la ~/.ssh/
# Should show: id_rsa, id_ed25519

# Test SSH key
ssh -T git@github.com

# Check Docker credentials
docker login
# Should use stored credentials

# Check AWS credentials
aws sts get-caller-identity
```

---

## Best Practices

### 1. **Use Strong Passphrases**

```bash
# ❌ Weak passphrase
password123

# ✅ Strong passphrase
correct-horse-battery-staple-2025!
```

Use a passphrase that is:
- At least 12 characters
- Contains letters, numbers, symbols
- Not used anywhere else
- Stored in a password manager

### 2. **Backup Your Encryption Key**

```bash
# Your age key is stored here:
~/.config/chezmoi/key.txt

# ⚠️ CRITICAL: Back this up to a safe location!
# Without it, you can't decrypt your secrets

# Options:
# - Password manager (recommended)
# - Encrypted USB drive
# - Paper backup in safe
# - Cloud storage (encrypted)
```

### 3. **Rotate Credentials After Restore**

```bash
# After restoring to a new machine, rotate sensitive credentials:

# 1. Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Add to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy and add to GitHub → Settings → SSH Keys

# 3. Remove old SSH key from GitHub
# (Delete the old key from GitHub settings)

# 4. Rotate cloud credentials
aws iam create-access-key
# Then delete old key

# 5. Rotate Docker credentials
docker login
# Use new credentials
```

### 4. **Use `.chezmoiignore` for Non-Sensitive Files**

```bash
# Create ~/.local/share/chezmoi/.chezmoiignore

# Don't backup these:
.bash_history
.cache/
.local/share/
.mozilla/firefox/*/sessionstore*
.config/google-chrome/*/History
```

### 5. **Regular Security Audits**

```bash
# Quarterly: Review what's backed up
chezmoi managed

# Check for accidentally committed secrets
cd ~/.local/share/chezmoi
git log --all --full-history -- "*password*"
git log --all --full-history -- "*secret*"

# If you find leaks:
# 1. Rotate the leaked credentials immediately
# 2. Use git filter-branch to remove from history
# 3. Force push to remote
```

### 6. **Separate Encryption for Different Secret Types**

```bash
# Use different age keys for different sensitivity levels

# Personal secrets
AGE_KEY_FILE=~/.config/chezmoi/personal-key.txt

# Work secrets
AGE_KEY_FILE=~/.config/chezmoi/work-key.txt

# High-security secrets
AGE_KEY_FILE=~/.config/chezmoi/critical-key.txt
```

---

## Enterprise Considerations

### Multi-User Scenarios

For teams sharing configurations:

```bash
# Use GPG with multiple recipients
chezmoi add --encrypt --recipient user1@company.com \
                      --recipient user2@company.com \
                      ~/.ssh/company_key
```

### Compliance Requirements

Organizations may require:
- **Audit logging** - Track who accesses what
- **Key rotation** - Mandatory credential expiry
- **Access control** - Not all team members get all secrets
- **Encryption standards** - Specific algorithms required

### Policy Example

```yaml
# company-secrets-policy.yaml
secrets:
  encryption:
    required: true
    algorithm: age  # or gpg
    min_passphrase_length: 16

  allowed_items:
    - ~/.ssh/id_rsa
    - ~/.docker/config.json
    - ~/.kube/config

  forbidden_items:
    - ~/.mozilla/firefox/  # Company policy
    - ~/.bash_history

  rotation:
    required: true
    interval_days: 90

  audit:
    enabled: true
    log_access: true
```

---

## Troubleshooting

### "Decryption Failed" Error

**Problem:** Can't decrypt secrets on new machine

**Solutions:**
```bash
# 1. Verify age key is present
ls ~/.config/chezmoi/key.txt

# 2. Copy age key from backup
# (from password manager or backup location)

# 3. Check age key permissions
chmod 600 ~/.config/chezmoi/key.txt

# 4. Test decryption manually
age --decrypt -i ~/.config/chezmoi/key.txt \
    ~/.local/share/chezmoi/encrypted_private_id_rsa.age
```

### "Permission Denied" for SSH Keys

**Problem:** SSH keys restored but can't use them

**Solution:**
```bash
# Fix permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Start SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```

### Accidentally Committed Unencrypted Secret

**Problem:** Plain text secret in Git history

**URGENT Solution:**
```bash
# 1. Immediately rotate the credential
# (Generate new SSH key, new API token, etc.)

# 2. Remove from Git history
cd ~/.local/share/chezmoi
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push
git push origin --force --all

# 4. Notify team (if applicable)
```

### Browser Profile Too Large

**Problem:** Browser profile backup takes forever

**Solution:**
```bash
# Don't backup cache/temporary files
# Add to .chezmoiignore:
.mozilla/firefox/*/cache2/
.mozilla/firefox/*/thumbnails/
.config/google-chrome/*/Cache/
.config/google-chrome/*/Service Worker/

# Only backup essential:
# - Bookmarks
# - Extensions
# - Settings
# - NOT: History, cache, cookies
```

---

## Security Checklist

Before backing up sensitive data:

- [ ] Encryption is enabled (age or GPG)
- [ ] Strong passphrase is used (12+ characters)
- [ ] Encryption key is backed up securely
- [ ] Repository is private (not public)
- [ ] You understand what's being backed up
- [ ] You have a credential rotation plan
- [ ] You're complying with company security policy
- [ ] `.chezmoiignore` excludes temporary files
- [ ] You've tested restore on a test machine first

After restore:

- [ ] All credentials work correctly
- [ ] SSH key is added to GitHub/GitLab
- [ ] Cloud credentials are tested
- [ ] Old credentials are rotated/removed
- [ ] File permissions are correct (600 for keys)
- [ ] Encryption key is secured on new machine

---

## Additional Resources

- [chezmoi Encryption Guide](https://www.chezmoi.io/user-guide/encryption/)
- [age Encryption Tool](https://age-encryption.org/)
- [GitHub: Managing SSH Keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [OWASP: Credential Storage Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## Quick Reference

### Common Commands

```bash
# Add encrypted file
chezmoi add --encrypt ~/.ssh/id_rsa

# Remove file from chezmoi
chezmoi forget ~/.ssh/id_rsa

# View encrypted file content
chezmoi cat ~/.ssh/id_rsa

# Check what's encrypted
cd ~/.local/share/chezmoi && ls *.age

# Re-encrypt with new key
chezmoi re-add --encrypt ~/.ssh/id_rsa

# Verify encryption
age --decrypt -i ~/.config/chezmoi/key.txt file.age
```

### Emergency: Leaked Credentials

1. **Immediately rotate** the leaked credential
2. **Remove from Git** history using `git filter-branch`
3. **Force push** to remote
4. **Notify affected parties** if applicable
5. **Review backup process** to prevent recurrence

---

## Questions?

- Check the [TuxSync FAQ](../README.md#faq)
- Report security issues: [SECURITY.md](../SECURITY.md)
- Ask on [GitHub Discussions](https://github.com/Gururagavendra/tuxsync/discussions)
