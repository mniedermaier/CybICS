#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to show help message
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|clean}"
    echo "  start   - Start the CybICS virtual environment"
    echo "  stop    - Stop the CybICS virtual environment"
    echo "  restart - Restart the CybICS virtual environment"
    echo "  status  - Show status of all services"
    echo "  logs    - Show logs from all services"
    echo "  clean   - Remove all CybICS containers, images, and volumes"
    exit 1
}

# Function to detect Docker Compose command
detect_docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        print_message "Error: Neither 'docker-compose' nor 'docker compose' is available." "$RED"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "Error: Docker is not running. Please start Docker first." "$RED"
        exit 1
    fi
}

# Function to start the environment
start_environment() {
    print_message "Starting CybICS virtual environment..." "$YELLOW"
    cd .devcontainer/virtual
    $DOCKER_COMPOSE up -d
    if [ $? -eq 0 ]; then
        print_message "CybICS virtual environment started successfully!" "$GREEN"
        print_message "\nAvailable services:" "$YELLOW"
        print_message "OpenPLC: http://localhost:8080" "$GREEN"
        print_message "FUXA: http://localhost:1881" "$GREEN"
        print_message "HWIO: http://localhost:80" "$GREEN"
        print_message "OPC UA: opc.tcp://localhost:4840" "$GREEN"
        print_message "S7 Communication: localhost:102" "$GREEN"
    else
        print_message "Error: Failed to start CybICS virtual environment." "$RED"
        exit 1
    fi
}

# Function to stop the environment
stop_environment() {
    print_message "Stopping CybICS virtual environment..." "$YELLOW"
    cd .devcontainer/virtual
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
    cd .devcontainer/virtual
    $DOCKER_COMPOSE ps
}

# Function to show logs
show_logs() {
    print_message "Showing logs for CybICS virtual environment..." "$YELLOW"
    cd .devcontainer/virtual
    $DOCKER_COMPOSE logs -f
}

# Function to remove all CybICS containers
remove_containers() {
    print_message "Removing all CybICS containers..." "$YELLOW"
    cd .devcontainer/virtual
    $DOCKER_COMPOSE down --rmi all --volumes --remove-orphans
    if [ $? -eq 0 ]; then
        print_message "All CybICS containers, images, and volumes removed successfully!" "$GREEN"
    else
        print_message "Error: Failed to remove CybICS containers." "$RED"
        exit 1
    fi
}

# Main script
check_docker
DOCKER_COMPOSE=$(detect_docker_compose)
print_message "Using Docker Compose command: $DOCKER_COMPOSE" "$YELLOW"

case "$1" in
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
    *)
        show_help
        ;;
esac 