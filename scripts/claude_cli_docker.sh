#!/bin/bash

# Claude CLI Docker Helper Script
# This script helps you use Claude Code CLI within the Docker container
# Updated for the new lightweight container configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                  Candlestick Nano - Claude CLI Docker                   ║"
    echo "║                         Enhanced Container Setup                        ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if API key is set
check_api_key() {
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "ANTHROPIC_API_KEY environment variable is not set."
        print_status "Please set it by running: export ANTHROPIC_API_KEY=your_api_key_here"
        print_status "Or add it to your .env file in the config directory."
        return 1
    fi
    return 0
}

# Function to start Claude CLI container
start_claude_container() {
    print_status "Starting Claude CLI container with enhanced configuration..."
    
    # Stop any existing claude-cli container
    docker-compose --profile claude down claude-cli 2>/dev/null || true
    
    # Build the image if needed
    print_status "Building/updating container image..."
    docker-compose build claude-cli
    
    # Start the Claude CLI container
    print_status "Starting container..."
    docker-compose --profile claude up -d claude-cli
    
    # Wait for container to be ready
    sleep 3
    
    if docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
        print_success "Claude CLI container started successfully!"
        print_status "Container name: candlestick-claude-cli"
        print_status "Working directory: /home/claude/workspace"
        print_status "Claude CLI should be available at: /home/claude/.local/bin/claude"
        echo
        print_status "To enter the container, run: $0 shell"
        print_status "To run Claude commands, use: $0 run \"<command>\""
    else
        print_error "Failed to start Claude CLI container"
        return 1
    fi
}

# Function to enter Claude CLI interactive mode
enter_claude_cli() {
    print_status "Entering Claude CLI interactive session..."
    print_status "You are now in the container as user 'claude'"
    print_status "Working directory: /home/claude/workspace"
    print_status "Your project files are mounted here"
    echo
    print_status "Available commands:"
    print_status "  - claude: Start Claude Code CLI"
    print_status "  - claude-check: Check Claude CLI version"
    print_status "  - python3: Run Python (venv is pre-activated)"
    print_status "  - Type 'exit' to leave the container shell"
    echo
    
    # Enter the container with proper shell setup
    docker exec -it --user claude candlestick-claude-cli zsh -l
}

# Function to run a single Claude command
run_claude_command() {
    local command="$1"
    print_status "Running Claude command: $command"
    echo
    
    # Run the command in the container
    docker exec -it --user claude candlestick-claude-cli bash -c "cd /home/claude/workspace && /home/claude/.local/bin/claude '$command'"
}

# Function to authenticate Claude CLI
authenticate_claude() {
    print_status "Starting Claude CLI authentication process..."
    print_warning "This will open an interactive session where you need to run 'claude' to authenticate"
    print_status "Follow the prompts to complete OAuth authentication"
    echo
    
    if ! docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
        print_warning "Claude CLI container is not running. Starting it first..."
        start_claude_container
        sleep 2
    fi
    
    docker exec -it --user claude candlestick-claude-cli bash -c "cd /home/claude/workspace && /home/claude/.local/bin/claude"
}

# Function to check Claude CLI status
check_claude_status() {
    print_status "Checking Claude CLI status..."
    echo
    
    if docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
        print_success "✓ Claude CLI container is running"
        
        # Check if Claude CLI is accessible
        if docker exec --user claude candlestick-claude-cli test -f /home/claude/.local/bin/claude; then
            print_success "✓ Claude CLI is installed and accessible"
            
            # Check Claude version
            local version=$(docker exec --user claude candlestick-claude-cli /home/claude/.local/bin/claude --version 2>/dev/null || echo "unknown")
            print_success "✓ Claude CLI version: $version"
            
            # Check if API key is configured
            if docker exec --user claude candlestick-claude-cli bash -c 'echo $ANTHROPIC_API_KEY' | grep -q "sk-"; then
                print_success "✓ API key is configured"
            else
                print_warning "⚠ API key may not be properly configured"
                print_status "Run '$0 auth' to authenticate Claude CLI"
            fi
            
            # Check if Claude is authenticated
            if docker exec --user claude candlestick-claude-cli bash -c 'test -f /home/claude/.anthropic/config.json'; then
                print_success "✓ Claude CLI appears to be authenticated"
            else
                print_warning "⚠ Claude CLI may not be authenticated"
                print_status "Run '$0 auth' to authenticate Claude CLI"
            fi
        else
            print_error "✗ Claude CLI is not accessible in container"
        fi
        
        # Check workspace mount
        if docker exec --user claude candlestick-claude-cli test -d /home/claude/workspace; then
            print_success "✓ Workspace is properly mounted"
        else
            print_error "✗ Workspace mount issue detected"
        fi
        
    else
        print_warning "✗ Claude CLI container is not running"
        print_status "Run '$0 start' to start the container"
    fi
}

# Function to stop Claude CLI container
stop_claude_container() {
    print_status "Stopping Claude CLI container..."
    docker-compose --profile claude down claude-cli
    print_success "Claude CLI container stopped"
}

# Function to rebuild container
rebuild_container() {
    print_status "Rebuilding Claude CLI container..."
    docker-compose --profile claude down claude-cli
    docker-compose build --no-cache claude-cli
    print_success "Container rebuilt successfully"
    print_status "Run '$0 start' to start the updated container"
}

# Function to show help
show_help() {
    print_banner
    echo "Claude CLI Docker Helper Script - Enhanced Version"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start               Start the Claude CLI container"
    echo "  stop                Stop the Claude CLI container"
    echo "  restart             Restart the Claude CLI container"
    echo "  shell               Enter interactive shell in the container"
    echo "  auth                Authenticate Claude CLI (required on first use)"
    echo "  run \"<command>\"     Run a specific Claude command"
    echo "  status              Check Claude CLI container status"
    echo "  rebuild             Rebuild the container from scratch"
    echo "  logs                Show container logs"
    echo "  help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start                          # Start Claude CLI container"
    echo "  $0 auth                           # Authenticate Claude CLI"
    echo "  $0 shell                          # Enter interactive mode"
    echo "  $0 run \"explain this codebase\"    # Run specific Claude command"
    echo "  $0 status                         # Check container status"
    echo "  $0 rebuild                        # Rebuild container"
    echo
    echo "Environment Variables:"
    echo "  ANTHROPIC_API_KEY                 # Your Claude API key (required)"
    echo
    echo "Development Container Support:"
    echo "  VS Code devcontainer is available in .devcontainer/"
    echo "  Open this project in VS Code and select 'Reopen in Container'"
    echo
    echo "Note: Make sure your ANTHROPIC_API_KEY is set before using Claude CLI"
}

# Function to show logs
show_logs() {
    print_status "Showing Claude CLI container logs..."
    docker-compose logs claude-cli
}

# Function to restart container
restart_container() {
    print_status "Restarting Claude CLI container..."
    stop_claude_container
    sleep 2
    start_claude_container
}

# Main script logic
print_banner

# Check Docker first
check_docker

case "${1:-help}" in
    start)
        start_claude_container
        ;;
    stop)
        stop_claude_container
        ;;
    restart)
        restart_container
        ;;
    shell)
        if ! docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
            print_warning "Claude CLI container is not running. Starting it first..."
            start_claude_container
            sleep 2
        fi
        enter_claude_cli
        ;;
    auth)
        authenticate_claude
        ;;
    run)
        if [ -z "$2" ]; then
            print_error "Please provide a command to run"
            print_status "Example: $0 run \"explain this codebase\""
            exit 1
        fi
        
        if ! docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
            print_warning "Claude CLI container is not running. Starting it first..."
            start_claude_container
            sleep 2
        fi
        
        run_claude_command "$2"
        ;;
    status)
        check_claude_status
        ;;
    rebuild)
        rebuild_container
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac 