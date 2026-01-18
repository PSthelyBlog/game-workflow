#!/bin/bash
#
# setup-butler.sh - Install and configure the butler CLI for itch.io uploads
#
# This script downloads butler (if not already installed) and helps configure
# authentication for itch.io game uploads.
#
# Usage:
#   ./scripts/setup-butler.sh
#   ./scripts/setup-butler.sh --install-only
#   ./scripts/setup-butler.sh --login-only
#
# Environment variables:
#   ITCHIO_API_KEY - If set, uses this key for authentication
#   BUTLER_PATH    - Custom installation directory (default: ~/.game-workflow/bin)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="${BUTLER_PATH:-$HOME/.game-workflow/bin}"

# Butler download base URL
BUTLER_BASE_URL="https://broth.itch.ovh/butler"

# Print colored message
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform
detect_platform() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)

    case "$os" in
        darwin)
            case "$arch" in
                arm64|aarch64)
                    echo "darwin-arm64"
                    ;;
                *)
                    echo "darwin-amd64"
                    ;;
            esac
            ;;
        linux)
            echo "linux-amd64"
            ;;
        mingw*|msys*|cygwin*)
            echo "windows-amd64"
            ;;
        *)
            print_error "Unsupported platform: $os $arch"
            exit 1
            ;;
    esac
}

# Check if butler is installed
check_butler() {
    if command -v butler &> /dev/null; then
        BUTLER_CMD="butler"
        return 0
    elif [ -x "$INSTALL_DIR/butler" ]; then
        BUTLER_CMD="$INSTALL_DIR/butler"
        return 0
    fi
    return 1
}

# Download and install butler
install_butler() {
    print_info "Installing butler to $INSTALL_DIR..."

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Detect platform
    local platform=$(detect_platform)
    local url="$BUTLER_BASE_URL/$platform/LATEST/archive/default"

    print_info "Downloading butler for $platform..."

    # Download
    local tmp_zip=$(mktemp)
    if command -v curl &> /dev/null; then
        curl -L -o "$tmp_zip" "$url" || {
            print_error "Failed to download butler"
            rm -f "$tmp_zip"
            exit 1
        }
    elif command -v wget &> /dev/null; then
        wget -O "$tmp_zip" "$url" || {
            print_error "Failed to download butler"
            rm -f "$tmp_zip"
            exit 1
        }
    else
        print_error "Neither curl nor wget is available"
        exit 1
    fi

    # Extract
    print_info "Extracting butler..."
    if command -v unzip &> /dev/null; then
        unzip -o "$tmp_zip" -d "$INSTALL_DIR" || {
            print_error "Failed to extract butler"
            rm -f "$tmp_zip"
            exit 1
        }
    else
        print_error "unzip is not available"
        rm -f "$tmp_zip"
        exit 1
    fi

    # Clean up
    rm -f "$tmp_zip"

    # Make executable
    chmod +x "$INSTALL_DIR/butler"

    # Set butler command
    BUTLER_CMD="$INSTALL_DIR/butler"

    print_success "Butler installed to $INSTALL_DIR/butler"

    # Add to PATH hint
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        print_info "To add butler to your PATH, add this to your shell profile:"
        echo ""
        echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
        echo ""
    fi
}

# Check butler version
show_version() {
    print_info "Butler version:"
    $BUTLER_CMD version
    echo ""
}

# Login to itch.io
login_butler() {
    print_info "Configuring itch.io authentication..."

    # Check if API key is provided via environment
    if [ -n "$ITCHIO_API_KEY" ]; then
        print_info "Using ITCHIO_API_KEY from environment..."
        # Butler reads the key from the environment automatically
        # We just need to verify it works
        if $BUTLER_CMD login --check &> /dev/null; then
            print_success "Already logged in to itch.io"
            return 0
        fi

        # Try to login with the API key
        echo "$ITCHIO_API_KEY" | $BUTLER_CMD login --api-key || {
            print_error "Failed to authenticate with ITCHIO_API_KEY"
            print_info "Please verify your API key is correct"
            exit 1
        }
        print_success "Logged in to itch.io using API key"
    else
        # Check if already logged in
        if $BUTLER_CMD login --check &> /dev/null; then
            print_success "Already logged in to itch.io"
            return 0
        fi

        # Interactive login
        print_info "Opening browser for itch.io authentication..."
        print_info "If the browser doesn't open, visit: https://itch.io/user/settings/api-keys"
        echo ""
        $BUTLER_CMD login || {
            print_error "Failed to login to itch.io"
            print_info "You can also set ITCHIO_API_KEY environment variable"
            exit 1
        }
        print_success "Logged in to itch.io"
    fi
}

# Show help
show_help() {
    echo "setup-butler.sh - Install and configure butler CLI for itch.io"
    echo ""
    echo "Usage:"
    echo "  ./scripts/setup-butler.sh              # Install and login"
    echo "  ./scripts/setup-butler.sh --install-only  # Install only"
    echo "  ./scripts/setup-butler.sh --login-only    # Login only"
    echo "  ./scripts/setup-butler.sh --help          # Show this help"
    echo ""
    echo "Environment variables:"
    echo "  ITCHIO_API_KEY  - API key for authentication (optional)"
    echo "  BUTLER_PATH     - Installation directory (default: ~/.game-workflow/bin)"
    echo ""
    echo "Getting an API key:"
    echo "  1. Visit https://itch.io/user/settings/api-keys"
    echo "  2. Click 'Generate new API key'"
    echo "  3. Set it as ITCHIO_API_KEY environment variable"
}

# Main
main() {
    local install_only=false
    local login_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --install-only)
                install_only=true
                shift
                ;;
            --login-only)
                login_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    echo ""
    echo "======================================"
    echo "     Butler CLI Setup for itch.io     "
    echo "======================================"
    echo ""

    # Install butler if needed
    if [ "$login_only" = false ]; then
        if check_butler; then
            print_success "Butler is already installed"
            show_version
        else
            install_butler
            show_version
        fi
    else
        if ! check_butler; then
            print_error "Butler is not installed. Run without --login-only first."
            exit 1
        fi
    fi

    # Login if needed
    if [ "$install_only" = false ]; then
        login_butler
    fi

    echo ""
    print_success "Butler setup complete!"
    echo ""
    echo "You can now upload games with:"
    echo "  butler push ./build username/game-name:html5"
    echo ""
    echo "Or use game-workflow to automate the entire process."
    echo ""
}

main "$@"
