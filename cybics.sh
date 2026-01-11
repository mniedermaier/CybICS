#!/bin/bash

# Change to script directory (repository root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || {
    echo "Error: Failed to change to script directory"
    exit 1
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
ORANGE='\033[38;5;208m'
NC='\033[0m' # No Color

# CybICS ASCII Art
print_banner() {
    print_message "
  ██████╗ ██╗   ██╗ ██████╗  ██╗  ██████╗ ███████╗
 ██╔════╝ ╚██╗ ██╔╝ ██╔══██╗ ██║ ██╔════╝ ██╔════╝
██║        ╚████╔ ╝ ██████╔╝ ██║ ██║      ███████╗
██║         ╚██╔╝   ██╔══██╗ ██║ ██║      ╚════██║
╚██████╔╝    ██║    ██████╔╝ ██║ ╚██████╗ ███████║
 ╚═════╝     ╚═╝    ╚═════╝ ╚═╝  ╚═════╝ ╚══════╝
" "$ORANGE"
    print_message "Cybersecurity testbed for Industrial Control Systems" "$ORANGE"
    print_message "========================================" "$ORANGE"
    echo
}

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to show help message
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|clean|compose} [--mode <mode>] [--version <tag>]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the CybICS virtual environment"
    echo "  stop    - Stop the CybICS virtual environment"
    echo "  restart - Restart the CybICS virtual environment"
    echo "  status  - Show status of all services"
    echo "  logs    - Show logs from all services"
    echo "  clean   - Remove all CybICS containers, images, and volumes"
    echo "  compose - Directly interact with docker compose (e.g., $0 compose ps)"
    echo ""
    echo "Options:"
    echo "  --mode <mode>    - Specify startup mode (default: full)"
    echo "                     minimal   - Core services only (OpenPLC, FUXA, HWIO, OPC UA, S7, Landing)"
    echo "                     full      - All services including AI Agent, Engineering WS, Attack Machine"
    echo "                     withoutai - All services except AI Agent"
    echo "  --version <tag>  - Specify Docker image version tag (default: latest)"
    echo "                     Examples: --version 1.0.0, --version abc1234, --version latest"
    exit 1
}

# Check if docker-compose or docker compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_message "Error: Neither 'docker-compose' nor 'docker compose' was found." "$RED"
    print_message "Please install Docker Compose:" "$RED"
    print_message "1. For Linux:" "$RED"
    print_message "   sudo apt-get update" "$RED"
    print_message "   sudo apt-get install docker-compose-plugin" "$RED"
    print_message "2. For macOS:" "$RED"
    print_message "   Install Docker Desktop from https://www.docker.com/products/docker-desktop" "$RED"
    print_message "3. For Windows:" "$RED"
    print_message "   Install Docker Desktop from https://www.docker.com/products/docker-desktop" "$RED"
    exit 1
fi

# Use docker compose if available, otherwise fall back to docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "Error: Docker is not running. Please start Docker first." "$RED"
        exit 1
    fi
}

# Function to ensure required environment files exist
ensure_env_files() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Create .docker.env directory if it doesn't exist
    if [ ! -d "$SCRIPT_DIR/.docker.env" ]; then
        print_message "Creating .docker.env directory..." "$YELLOW"
        mkdir -p "$SCRIPT_DIR/.docker.env"
        print_message ".docker.env directory created successfully!" "$GREEN"
    fi

    # Check if .env exists, if not create it with default values
    if [ ! -f .env ]; then
        print_message "Creating .env file with default values..." "$YELLOW"
        cat > .env << EOF
HOST_UID=1000
HOST_GID=1000
DOCKER_ENV_DIR="$SCRIPT_DIR/.docker.env"
EOF
        print_message ".env file created successfully!" "$GREEN"
    fi

    # Check if .dev.env exists, if not create it with default values
    if [ ! -f .dev.env ]; then
        print_message "Creating .dev.env file with default values..." "$YELLOW"
        cat > .dev.env << 'EOF'
DEVICE_IP=cybics
DEVICE_USER=pi
EOF
        print_message ".dev.env file created successfully!" "$GREEN"
    fi
}

# Function to find conflicting networks
find_conflicting_networks() {
    local target_subnet="$1"
    # Extract the network prefix (e.g., 172.19.0 from 172.19.0.0/24)
    local prefix=$(echo "$target_subnet" | sed 's/\.[0-9]*\/.*$//')

    # Find networks that might overlap
    docker network ls --format '{{.Name}}' | while read network; do
        local subnet=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null)
        if [[ "$subnet" == *"$prefix"* ]]; then
            echo "$network"
        fi
    done
}

# Function to handle network overlap error
handle_network_overlap() {
    local error_output="$1"

    # Check if this is a network overlap error
    if echo "$error_output" | grep -q "Pool overlaps with other one on this address space"; then
        print_message "\nNetwork conflict detected!" "$YELLOW"
        print_message "Another Docker network is using the same IP range." "$YELLOW"

        # Try to find conflicting networks (check common CybICS subnets)
        print_message "\nSearching for conflicting networks..." "$YELLOW"
        local conflicting=""

        # Check for networks with similar subnets
        for network in $(docker network ls --format '{{.Name}}' | grep -v "bridge\|host\|none"); do
            local subnet=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null)
            if [[ -n "$subnet" ]]; then
                # Check if it's in the 172.18.x.x or 172.19.x.x range (common for CybICS)
                if [[ "$subnet" == 172.1[89].* ]] || [[ "$subnet" == 10.0.* ]]; then
                    if [[ -z "$conflicting" ]]; then
                        conflicting="$network ($subnet)"
                    else
                        conflicting="$conflicting, $network ($subnet)"
                    fi
                fi
            fi
        done

        if [[ -n "$conflicting" ]]; then
            print_message "Potentially conflicting networks: $conflicting" "$YELLOW"
        fi

        # List all custom networks for user reference
        print_message "\nAll custom Docker networks:" "$BLUE"
        docker network ls --format 'table {{.Name}}\t{{.Driver}}' | grep -v "bridge\|host\|none" | head -20

        echo
        print_message "Would you like to remove conflicting networks and retry? (y/n)" "$YELLOW"
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_message "\nWhich network would you like to remove?" "$YELLOW"
            print_message "Enter network name (or 'all' to remove all custom networks, 'cancel' to abort):" "$YELLOW"
            read -r network_name

            if [[ "$network_name" == "cancel" ]]; then
                print_message "Operation cancelled." "$YELLOW"
                return 1
            elif [[ "$network_name" == "all" ]]; then
                print_message "Removing all custom networks..." "$YELLOW"
                for network in $(docker network ls --format '{{.Name}}' | grep -v "bridge\|host\|none"); do
                    docker network rm "$network" 2>/dev/null && \
                        print_message "Removed network: $network" "$GREEN"
                done
                return 0
            elif [[ -n "$network_name" ]]; then
                if docker network rm "$network_name" 2>/dev/null; then
                    print_message "Removed network: $network_name" "$GREEN"
                    return 0
                else
                    print_message "Failed to remove network: $network_name" "$RED"
                    print_message "The network might be in use. Try stopping containers first with: ./cybics.sh stop" "$YELLOW"
                    return 1
                fi
            fi
        fi
        return 1
    fi
    return 1
}

# Function to display available services based on mode
display_services() {
    print_message "CybICS virtual environment started successfully!" "$GREEN"
    print_message "\nAvailable services:" "$YELLOW"
    print_message "Landing page: http://localhost:80" "$GREEN"
    print_message "OpenPLC: http://localhost:8080" "$GREEN"
    print_message "FUXA: http://localhost:1881" "$GREEN"
    print_message "HWIO: http://localhost:8090" "$GREEN"

    # Display optional services based on mode
    if [[ "$CYBICS_MODE" == "full" || "$CYBICS_MODE" == "withoutai" ]]; then
        print_message "Engineering Workstation (VNC): http://localhost:6080/vnc.html" "$GREEN"
        print_message "Attack Machine (VNC): http://localhost:6081/vnc.html" "$GREEN"
    fi

    print_message "OPC UA: opc.tcp://localhost:4840" "$GREEN"
    print_message "S7 Communication: localhost:102" "$GREEN"

    if [[ "$CYBICS_MODE" == "full" ]]; then
        print_message "CybICS AI Agent: Available via Landing Page" "$GREEN"
    fi
}

# Function to start the environment
start_environment() {
    print_message "Starting CybICS virtual environment..." "$YELLOW"
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }

    # Capture both stdout and stderr
    local output
    output=$($DOCKER_COMPOSE up -d 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        display_services
    else
        echo "$output"

        # Check for network overlap error and handle it
        if handle_network_overlap "$output"; then
            print_message "\nRetrying startup..." "$YELLOW"
            $DOCKER_COMPOSE up -d
            if [ $? -eq 0 ]; then
                display_services
                return
            fi
        fi

        print_message "Error: Failed to start CybICS virtual environment." "$RED"
        exit 1
    fi
}

# Function to stop the environment
stop_environment() {
    print_message "Stopping CybICS virtual environment..." "$YELLOW"
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }
    $DOCKER_COMPOSE down
    if [ $? -eq 0 ]; then
        print_message "CybICS virtual environment stopped successfully!" "$GREEN"
    else
        print_message "Error: Failed to stop CybICS virtual environment." "$RED"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_message "Checking CybICS virtual environment status..." "$YELLOW"
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }
    $DOCKER_COMPOSE ps
}

# Function to show logs
show_logs() {
    print_message "Showing logs for CybICS virtual environment..." "$YELLOW"
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }
    $DOCKER_COMPOSE logs -f
}

# Function to remove all CybICS containers
remove_containers() {
    print_message "Removing all CybICS containers..." "$YELLOW"
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }
    $DOCKER_COMPOSE down --rmi all --volumes --remove-orphans
    if [ $? -eq 0 ]; then
        print_message "All CybICS containers, images, and volumes removed successfully!" "$GREEN"
    else
        print_message "Error: Failed to remove CybICS containers." "$RED"
        exit 1
    fi
}

# Function to directly interact with docker compose
direct_compose() {
    cd "$SCRIPT_DIR/.devcontainer/virtual" || {
        print_message "Error: Cannot access .devcontainer/virtual directory" "$RED"
        exit 1
    }
    $DOCKER_COMPOSE "$@"
}

# Main script
print_banner
check_docker
ensure_env_files
print_message "Using Docker Compose command: $DOCKER_COMPOSE" "$YELLOW"

# Parse arguments for version and mode options
CYBICS_VERSION="latest"
CYBICS_MODE="full"
COMMAND=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            if [[ -n "$2" && "$2" != --* ]]; then
                CYBICS_VERSION="$2"
                shift 2
            else
                print_message "Error: --version requires a tag argument" "$RED"
                show_help
            fi
            ;;
        --mode)
            if [[ -n "$2" && "$2" != --* ]]; then
                CYBICS_MODE="$2"
                if [[ "$CYBICS_MODE" != "minimal" && "$CYBICS_MODE" != "full" && "$CYBICS_MODE" != "withoutai" ]]; then
                    print_message "Error: Invalid mode '$CYBICS_MODE'. Must be: minimal, full, or withoutai" "$RED"
                    show_help
                fi
                shift 2
            else
                print_message "Error: --mode requires an argument" "$RED"
                show_help
            fi
            ;;
        start|stop|restart|status|logs|clean|compose)
            COMMAND="$1"
            shift
            # For 'compose' command, save remaining arguments
            if [[ "$COMMAND" == "compose" ]]; then
                COMPOSE_ARGS="$@"
                break
            fi
            ;;
        *)
            if [[ -z "$COMMAND" ]]; then
                show_help
            else
                # Unknown option after command
                print_message "Error: Unknown option: $1" "$RED"
                show_help
            fi
            ;;
    esac
done

# Export version for docker-compose
export CYBICS_VERSION

# Set COMPOSE_PROFILES based on mode
case "$CYBICS_MODE" in
    "minimal")
        export COMPOSE_PROFILES=""
        ;;
    "full")
        export COMPOSE_PROFILES="full,attack,engineering,ai"
        ;;
    "withoutai")
        export COMPOSE_PROFILES="attack,engineering"
        ;;
esac

if [[ "$CYBICS_VERSION" != "latest" ]]; then
    print_message "Using Docker image version: $CYBICS_VERSION" "$BLUE"
fi

if [[ "$CYBICS_MODE" != "full" ]]; then
    print_message "Using startup mode: $CYBICS_MODE" "$BLUE"
fi

case "$COMMAND" in
    "start")
        start_environment
        ;;
    "stop")
        stop_environment
        ;;
    "restart")
        stop_environment
        start_environment
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        remove_containers
        ;;
    "compose")
        direct_compose $COMPOSE_ARGS
        ;;
    *)
        show_help
        ;;
esac 
