#!/bin/bash

# Claude CLI Docker Helper Script
# This script helps you use Claude Code CLI within the Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    print_warning "ANTHROPIC_API_KEY environment variable is not set."
    print_status "Please set it by running: export ANTHROPIC_API_KEY=your_api_key_here"
    print_status "Or add it to your .env file in the config directory."
fi

# Function to start Claude CLI container
start_claude_container() {
    print_status "Starting Claude CLI container..."
    
    # Stop any existing claude-cli container
    docker-compose --profile claude down claude-cli 2>/dev/null || true
    
    # Start the Claude CLI container
    docker-compose --profile claude up -d claude-cli
    
    print_success "Claude CLI container started successfully!"
    print_status "Container name: candlestick-claude-cli"
}

# Function to enter Claude CLI interactive mode
enter_claude_cli() {
    print_status "Entering Claude CLI interactive session..."
    print_status "Type 'exit' to leave the container shell"
    print_status "Use 'claude' command to start Claude Code CLI"
    echo
    
    docker exec -it candlestick-claude-cli bash
}

# Function to run a single Claude command
run_claude_command() {
    local command="$1"
    print_status "Running Claude command: $command"
    
    docker exec -it candlestick-claude-cli bash -c "cd /app && claude '$command'"
}

# Function to check Claude CLI status
check_claude_status() {
    print_status "Checking Claude CLI status..."
    
    if docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
        print_success "Claude CLI container is running"
        
        # Check if Claude CLI is accessible
        if docker exec candlestick-claude-cli which claude >/dev/null 2>&1; then
            print_success "Claude CLI is installed and accessible"
            
            # Check if API key is configured
            if docker exec candlestick-claude-cli bash -c 'echo $ANTHROPIC_API_KEY' | grep -q "sk-"; then
                print_success "API key is configured"
            else
                print_warning "API key may not be properly configured"
            fi
        else
            print_error "Claude CLI is not accessible in container"
        fi
    else
        print_warning "Claude CLI container is not running"
        print_status "Run '$0 start' to start the container"
    fi
}

# Function to stop Claude CLI container
stop_claude_container() {
    print_status "Stopping Claude CLI container..."
    docker-compose --profile claude down claude-cli
    print_success "Claude CLI container stopped"
}

# Function to show help
show_help() {
    echo "Claude CLI Docker Helper Script"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start               Start the Claude CLI container"
    echo "  stop                Stop the Claude CLI container"
    echo "  shell               Enter interactive shell in the container"
    echo "  run \"<command>\"     Run a specific Claude command"
    echo "  status              Check Claude CLI container status"
    echo "  help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start                          # Start Claude CLI container"
    echo "  $0 shell                          # Enter interactive mode"
    echo "  $0 run \"explain this codebase\"    # Run specific Claude command"
    echo "  $0 status                         # Check container status"
    echo
    echo "Environment Variables:"
    echo "  ANTHROPIC_API_KEY                 # Your Claude API key (required)"
    echo
    echo "Note: Make sure your ANTHROPIC_API_KEY is set before using Claude CLI"
}

# Main script logic
case "${1:-help}" in
    start)
        start_claude_container
        ;;
    stop)
        stop_claude_container
        ;;
    shell)
        if ! docker ps --format "table {{.Names}}" | grep -q "candlestick-claude-cli"; then
            print_warning "Claude CLI container is not running. Starting it first..."
            start_claude_container
            sleep 2
        fi
        enter_claude_cli
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
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 