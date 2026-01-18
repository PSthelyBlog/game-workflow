#!/bin/bash
#
# setup-slack-app.sh - Helper for setting up a Slack app for game-workflow
#
# This script guides you through creating a Slack app with the required
# permissions for the game-workflow approval system.
#
# Usage:
#   ./scripts/setup-slack-app.sh
#
# The script will:
#   1. Display the required OAuth scopes
#   2. Generate a Slack app manifest
#   3. Provide step-by-step setup instructions
#   4. Help test the connection
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

print_step() {
    echo -e "${CYAN}==> $1${NC}"
}

# Show help
show_help() {
    echo "setup-slack-app.sh - Helper for Slack app setup"
    echo ""
    echo "Usage:"
    echo "  ./scripts/setup-slack-app.sh              # Interactive setup"
    echo "  ./scripts/setup-slack-app.sh --manifest   # Generate manifest only"
    echo "  ./scripts/setup-slack-app.sh --test       # Test existing token"
    echo "  ./scripts/setup-slack-app.sh --help       # Show this help"
    echo ""
    echo "Environment variables:"
    echo "  SLACK_BOT_TOKEN  - Bot token to test (for --test)"
    echo "  SLACK_CHANNEL    - Channel to test posting to"
}

# Generate Slack app manifest
generate_manifest() {
    local app_name="${1:-Game Workflow}"

    cat << 'MANIFEST'
display_information:
  name: Game Workflow
  description: Automated game creation workflow with human approval gates
  background_color: "#4A154B"

features:
  bot_user:
    display_name: Game Workflow
    always_online: true

oauth_config:
  scopes:
    bot:
      - chat:write
      - chat:write.public
      - reactions:read
      - channels:history
      - groups:history
      - im:history
      - mpim:history

settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
MANIFEST
}

# Display required permissions
show_permissions() {
    echo ""
    print_step "Required OAuth Scopes"
    echo ""
    echo "Your Slack app needs the following Bot Token Scopes:"
    echo ""
    echo "  ${GREEN}chat:write${NC}         - Post messages to channels"
    echo "  ${GREEN}chat:write.public${NC}  - Post to channels the bot isn't in"
    echo "  ${GREEN}reactions:read${NC}     - Read reactions on messages"
    echo "  ${GREEN}channels:history${NC}   - Read messages in public channels"
    echo "  ${GREEN}groups:history${NC}     - Read messages in private channels"
    echo "  ${GREEN}im:history${NC}         - Read direct messages"
    echo "  ${GREEN}mpim:history${NC}       - Read group direct messages"
    echo ""
}

# Test Slack connection
test_connection() {
    local token="${SLACK_BOT_TOKEN:-}"
    local channel="${SLACK_CHANNEL:-}"

    if [ -z "$token" ]; then
        print_error "SLACK_BOT_TOKEN is not set"
        echo ""
        echo "Set it with:"
        echo "  export SLACK_BOT_TOKEN=xoxb-your-token-here"
        return 1
    fi

    print_info "Testing Slack connection..."

    # Test auth
    local auth_response
    auth_response=$(curl -s -X POST "https://slack.com/api/auth.test" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json")

    if echo "$auth_response" | grep -q '"ok":true'; then
        local bot_name
        bot_name=$(echo "$auth_response" | grep -o '"user":"[^"]*"' | cut -d'"' -f4)
        local team
        team=$(echo "$auth_response" | grep -o '"team":"[^"]*"' | cut -d'"' -f4)
        print_success "Connected as @$bot_name in workspace: $team"
    else
        local error
        error=$(echo "$auth_response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
        print_error "Authentication failed: $error"
        return 1
    fi

    # Test posting if channel is set
    if [ -n "$channel" ]; then
        print_info "Testing message posting to $channel..."

        local post_response
        post_response=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "{\"channel\":\"$channel\",\"text\":\"Test message from game-workflow setup script. This can be deleted.\"}")

        if echo "$post_response" | grep -q '"ok":true'; then
            print_success "Successfully posted test message to $channel"

            # Get message timestamp for deletion offer
            local ts
            ts=$(echo "$post_response" | grep -o '"ts":"[^"]*"' | cut -d'"' -f4)

            echo ""
            read -p "Delete the test message? (y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                curl -s -X POST "https://slack.com/api/chat.delete" \
                    -H "Authorization: Bearer $token" \
                    -H "Content-Type: application/json" \
                    -d "{\"channel\":\"$channel\",\"ts\":\"$ts\"}" > /dev/null
                print_success "Test message deleted"
            fi
        else
            local error
            error=$(echo "$post_response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
            print_warn "Could not post to $channel: $error"
            print_info "Make sure the bot is invited to the channel"
        fi
    fi

    return 0
}

# Interactive setup guide
interactive_setup() {
    echo ""
    echo "======================================"
    echo "     Slack App Setup for game-workflow"
    echo "======================================"
    echo ""

    show_permissions

    print_step "Step 1: Create a Slack App"
    echo ""
    echo "1. Go to: ${CYAN}https://api.slack.com/apps${NC}"
    echo "2. Click '${GREEN}Create New App${NC}'"
    echo "3. Choose '${GREEN}From scratch${NC}'"
    echo "4. Name it '${GREEN}Game Workflow${NC}' and select your workspace"
    echo ""
    read -p "Press Enter when you've created the app..."
    echo ""

    print_step "Step 2: Configure OAuth Scopes"
    echo ""
    echo "1. In your app settings, go to '${GREEN}OAuth & Permissions${NC}'"
    echo "2. Scroll to '${GREEN}Scopes${NC}' > '${GREEN}Bot Token Scopes${NC}'"
    echo "3. Click '${GREEN}Add an OAuth Scope${NC}' and add each of these:"
    echo ""
    echo "   - chat:write"
    echo "   - chat:write.public"
    echo "   - reactions:read"
    echo "   - channels:history"
    echo "   - groups:history"
    echo "   - im:history"
    echo "   - mpim:history"
    echo ""
    read -p "Press Enter when you've added all scopes..."
    echo ""

    print_step "Step 3: Install App to Workspace"
    echo ""
    echo "1. Scroll up to '${GREEN}OAuth Tokens for Your Workspace${NC}'"
    echo "2. Click '${GREEN}Install to Workspace${NC}'"
    echo "3. Review permissions and click '${GREEN}Allow${NC}'"
    echo "4. Copy the '${GREEN}Bot User OAuth Token${NC}' (starts with xoxb-)"
    echo ""
    read -p "Press Enter when you have the token..."
    echo ""

    print_step "Step 4: Configure Environment"
    echo ""
    echo "Add the token to your environment:"
    echo ""
    echo "  ${GREEN}export SLACK_BOT_TOKEN=xoxb-your-token-here${NC}"
    echo "  ${GREEN}export SLACK_CHANNEL=#game-dev${NC}"
    echo ""
    echo "Or add to ~/.game-workflow/config.toml:"
    echo ""
    echo "  ${GREEN}[slack]${NC}"
    echo "  ${GREEN}channel = \"#game-dev\"${NC}"
    echo ""
    read -p "Press Enter when you've set the environment variables..."
    echo ""

    print_step "Step 5: Invite Bot to Channel"
    echo ""
    echo "1. Go to your Slack workspace"
    echo "2. Open the channel you want to use (e.g., #game-dev)"
    echo "3. Type: ${GREEN}/invite @Game Workflow${NC}"
    echo ""
    read -p "Press Enter when you've invited the bot..."
    echo ""

    print_step "Step 6: Test Connection"
    echo ""

    if [ -n "$SLACK_BOT_TOKEN" ]; then
        test_connection
    else
        print_warn "SLACK_BOT_TOKEN is not set"
        echo ""
        echo "To test the connection, set the environment variables and run:"
        echo "  ${GREEN}./scripts/setup-slack-app.sh --test${NC}"
    fi

    echo ""
    print_success "Slack app setup complete!"
    echo ""
    echo "Usage in game-workflow:"
    echo "  - Approval requests will be sent to your Slack channel"
    echo "  - React with :white_check_mark: to approve"
    echo "  - React with :x: to reject"
    echo "  - Reply in thread with feedback"
    echo ""
}

# Main
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --manifest)
                generate_manifest
                exit 0
                ;;
            --test)
                test_connection
                exit $?
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

    # Default: interactive setup
    interactive_setup
}

main "$@"
