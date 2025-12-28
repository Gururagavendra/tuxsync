#!/usr/bin/env bash
#
# TuxSync Remote Restore Script
# Usage: curl -sL https://raw.githubusercontent.com/Gururagavendra/tuxsync/main/restore.sh | bash -s -- <GIST_ID>
#

set -e

GIST_ID="${1:-}"
TUXSYNC_VERSION="0.1.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║     TuxSync Remote Restore v${TUXSYNC_VERSION}       ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check for required tools
check_deps() {
    local missing=()

    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        missing+=("curl or wget")
    fi

    if ! command -v gh &> /dev/null; then
        missing+=("gh (GitHub CLI)")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Please install them and try again."
        exit 1
    fi
}

# Detect package manager
detect_pm() {
    if command -v apt &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

# Install packages based on package manager
install_packages() {
    local pm="$1"
    shift
    local packages=("$@")

    if [ ${#packages[@]} -eq 0 ]; then
        log_warn "No packages to install"
        return 0
    fi

    log_info "Installing ${#packages[@]} packages using $pm..."

    case "$pm" in
        apt)
            sudo apt update
            sudo apt install -y "${packages[@]}"
            ;;
        dnf)
            sudo dnf install -y "${packages[@]}"
            ;;
        pacman)
            sudo pacman -Sy --noconfirm "${packages[@]}"
            ;;
        *)
            log_error "Unknown package manager: $pm"
            return 1
            ;;
    esac
}

# Main restore function
restore() {
    local gist_id="$1"

    if [ -z "$gist_id" ]; then
        log_error "Usage: restore.sh <GIST_ID>"
        echo "Example: curl -sL .../restore.sh | bash -s -- abc123def456"
        exit 1
    fi

    print_banner
    log_info "Restoring from backup: $gist_id"

    # Check dependencies
    check_deps

    # Create temp directory
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    # Fetch tuxsync.yaml from gist
    log_info "Fetching backup metadata..."
    if ! gh gist view "$gist_id" --raw -f tuxsync.yaml > "$TMP_DIR/tuxsync.yaml" 2>/dev/null; then
        log_error "Failed to fetch backup. Check the Gist ID and ensure you're logged in (gh auth login)"
        exit 1
    fi

    # Parse YAML (basic parsing without dependencies)
    log_info "Parsing backup..."

    # Extract distro info
    source_distro=$(grep "^distro:" "$TMP_DIR/tuxsync.yaml" | cut -d: -f2 | xargs)
    source_version=$(grep "^distro_version:" "$TMP_DIR/tuxsync.yaml" | cut -d: -f2 | xargs)
    source_pm=$(grep "^package_manager:" "$TMP_DIR/tuxsync.yaml" | cut -d: -f2 | xargs)

    log_info "Source system: $source_distro $source_version ($source_pm)"

    # Detect current system
    current_pm=$(detect_pm)
    log_info "Current system package manager: $current_pm"

    # Warning if package managers differ
    if [ "$source_pm" != "$current_pm" ]; then
        log_warn "Package manager mismatch! Source: $source_pm, Current: $current_pm"
        log_warn "Some packages may not be available or have different names."
        echo -n "Continue anyway? [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Restore cancelled"
            exit 0
        fi
    fi

    # Extract packages (between 'packages:' and next key)
    log_info "Extracting package list..."
    packages=()
    in_packages=false
    while IFS= read -r line; do
        if [[ "$line" =~ ^packages: ]]; then
            in_packages=true
            continue
        fi
        if [[ "$in_packages" == true ]]; then
            if [[ "$line" =~ ^[a-z_]+: ]]; then
                break
            fi
            if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*(.*) ]]; then
                pkg="${BASH_REMATCH[1]}"
                packages+=("$pkg")
            fi
        fi
    done < "$TMP_DIR/tuxsync.yaml"

    log_info "Found ${#packages[@]} packages to install"

    # Show package list
    echo ""
    echo "Packages to install:"
    for pkg in "${packages[@]}"; do
        echo "  - $pkg"
    done | head -20
    if [ ${#packages[@]} -gt 20 ]; then
        echo "  ... and $((${#packages[@]} - 20)) more"
    fi
    echo ""

    # Confirm
    echo -n "Proceed with installation? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    # Install packages
    install_packages "$current_pm" "${packages[@]}"

    # Restore bashrc if present
    has_bashrc=$(grep "^has_bashrc:" "$TMP_DIR/tuxsync.yaml" | cut -d: -f2 | xargs)
    if [ "$has_bashrc" = "true" ]; then
        log_info "Fetching .bashrc..."
        if gh gist view "$gist_id" --raw -f bashrc > "$TMP_DIR/bashrc" 2>/dev/null; then
            echo -n "Restore .bashrc? (existing will be backed up) [y/N] "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                if [ -f "$HOME/.bashrc" ]; then
                    cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
                    log_info "Existing .bashrc backed up"
                fi
                cp "$TMP_DIR/bashrc" "$HOME/.bashrc"
                log_info ".bashrc restored!"
            fi
        fi
    fi

    echo ""
    log_info "═══ Restore Complete! ═══"
    log_info "You may need to:"
    echo "  1. Restart your terminal or run: source ~/.bashrc"
    echo "  2. Log out and back in for some changes to take effect"
    echo ""
}

restore "$GIST_ID"
