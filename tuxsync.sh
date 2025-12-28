#!/usr/bin/env bash
#
# TuxSync - Profile Sync for Linux
# Entry wrapper script that checks dependencies and forwards commands
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_ENTRY="$SCRIPT_DIR/src/tuxsync/cli.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║          TuxSync v0.1.0                ║"
    echo "║   Profile Sync for Linux Users         ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Detect package manager
detect_package_manager() {
    if command_exists apt; then
        echo "apt"
    elif command_exists dnf; then
        echo "dnf"
    elif command_exists pacman; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

# Install a package using the detected package manager
install_package() {
    local pkg_name="$1"
    local pkg_manager
    pkg_manager=$(detect_package_manager)
    
    case "$pkg_manager" in
        apt)
            sudo apt update && sudo apt install -y "$pkg_name"
            ;;
        dnf)
            sudo dnf install -y "$pkg_name"
            ;;
        pacman)
            sudo pacman -Sy --noconfirm "$pkg_name"
            ;;
        *)
            log_error "Unknown package manager. Please install $pkg_name manually."
            return 1
            ;;
    esac
}

# Install gum (requires special handling)
install_gum() {
    local pkg_manager
    pkg_manager=$(detect_package_manager)
    
    case "$pkg_manager" in
        apt)
            # Install gum from Charm's repository for Debian/Ubuntu
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
            echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
            sudo apt update && sudo apt install -y gum
            ;;
        dnf)
            # Install gum from Charm's repository for Fedora
            echo '[charm]
name=Charm
baseurl=https://repo.charm.sh/yum/
enabled=1
gpgcheck=1
gpgkey=https://repo.charm.sh/yum/gpg.key' | sudo tee /etc/yum.repos.d/charm.repo
            sudo dnf install -y gum
            ;;
        pacman)
            # gum is available in AUR or community repo
            sudo pacman -Sy --noconfirm gum 2>/dev/null || {
                log_warn "gum not in official repos. Attempting AUR install..."
                if command_exists yay; then
                    yay -S --noconfirm gum
                elif command_exists paru; then
                    paru -S --noconfirm gum
                else
                    log_error "Please install gum from AUR manually: yay -S gum"
                    return 1
                fi
            }
            ;;
        *)
            log_error "Unknown package manager. Please install gum manually from https://github.com/charmbracelet/gum"
            return 1
            ;;
    esac
}

# Install gh (GitHub CLI)
install_gh() {
    local pkg_manager
    pkg_manager=$(detect_package_manager)
    
    case "$pkg_manager" in
        apt)
            # Install gh from GitHub's official repository
            type -p curl >/dev/null || sudo apt install curl -y
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update && sudo apt install -y gh
            ;;
        dnf)
            sudo dnf install -y gh
            ;;
        pacman)
            sudo pacman -Sy --noconfirm github-cli
            ;;
        *)
            log_error "Unknown package manager. Please install gh manually from https://cli.github.com/"
            return 1
            ;;
    esac
}

# Check and install dependencies
check_dependencies() {
    local missing_deps=()
    
    # Check Python 3
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    # Check gum
    if ! command_exists gum; then
        missing_deps+=("gum")
    fi
    
    # Check gh (GitHub CLI)
    if ! command_exists gh; then
        missing_deps+=("gh")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        return 0
    fi
    
    log_warn "The following dependencies are missing: ${missing_deps[*]}"
    
    # If gum is available, use it for interactive prompt
    if command_exists gum; then
        if gum confirm "Would you like to install them now?"; then
            install_missing_deps "${missing_deps[@]}"
        else
            log_error "Cannot proceed without required dependencies."
            exit 1
        fi
    else
        # Fallback to basic prompt
        echo -n "Would you like to install them now? [y/N] "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            install_missing_deps "${missing_deps[@]}"
        else
            log_error "Cannot proceed without required dependencies."
            exit 1
        fi
    fi
}

# Install missing dependencies
install_missing_deps() {
    for dep in "$@"; do
        log_info "Installing $dep..."
        case "$dep" in
            python3)
                install_package python3
                ;;
            gum)
                install_gum
                ;;
            gh)
                install_gh
                ;;
        esac
        
        if [ $? -eq 0 ]; then
            log_info "$dep installed successfully!"
        else
            log_error "Failed to install $dep"
            exit 1
        fi
    done
}

# Show help
show_help() {
    print_banner
    echo "Usage: tuxsync <command> [options]"
    echo ""
    echo "Commands:"
    echo "  backup              Create a backup of installed packages and configs"
    echo "  restore <ID>        Restore packages and configs from a backup ID"
    echo "  list                List available backups"
    echo "  version             Show version information"
    echo "  help                Show this help message"
    echo ""
    echo "Options:"
    echo "  --no-bashrc         Skip backing up ~/.bashrc"
    echo "  --github            Use GitHub Gist for storage"
    echo "  --server <URL>      Use custom server for storage"
    echo ""
    echo "Examples:"
    echo "  tuxsync backup                    # Interactive backup"
    echo "  tuxsync backup --github           # Backup to GitHub Gist"
    echo "  tuxsync restore abc123            # Restore from Gist ID"
    echo ""
}

# Main entry point
main() {
    # Check dependencies first
    check_dependencies
    
    case "${1:-}" in
        backup|restore|list)
            # Forward to Python CLI
            if command_exists uv && [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
                cd "$SCRIPT_DIR" && uv run tuxsync "$@"
            elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
                "$SCRIPT_DIR/.venv/bin/python" -m tuxsync "$@"
            else
                python3 -m tuxsync "$@"
            fi
            ;;
        version|--version|-v)
            print_banner
            echo "TuxSync version 0.1.0"
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
