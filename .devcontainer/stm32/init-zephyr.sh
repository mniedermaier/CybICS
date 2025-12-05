#!/bin/bash
# Initialize Zephyr workspace if it doesn't exist

set -e

ZEPHYR_DIR="$HOME/zephyrproject"

if [ ! -d "$ZEPHYR_DIR" ]; then
    echo "Initializing Zephyr workspace at $ZEPHYR_DIR..."

    # Create workspace directory
    mkdir -p "$ZEPHYR_DIR"
    cd "$ZEPHYR_DIR"

    # Initialize west workspace
    west init -m https://github.com/zephyrproject-rtos/zephyr --mr v3.5.0

    # Update all modules
    west update

    # Export Zephyr CMake package
    west zephyr-export

    # Install Python dependencies
    pip3 install --user -r zephyr/scripts/requirements.txt

    echo "Zephyr workspace initialized successfully!"
    echo "You can now build Zephyr projects with: west build -b <board>"
else
    echo "Zephyr workspace already exists at $ZEPHYR_DIR"
fi

# Set up environment variables
export ZEPHYR_BASE="$ZEPHYR_DIR/zephyr"

# Add convenience aliases to bashrc if not already present
if ! grep -q "alias zephyr-env" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" << 'EOF'

# Python user bin directory
export PATH=$HOME/.local/bin:$PATH

# Zephyr environment
alias zephyr-env='export ZEPHYR_BASE=$HOME/zephyrproject/zephyr'
alias zephyr-cd='cd $HOME/zephyrproject'

# Auto-activate Zephyr environment
export ZEPHYR_BASE=$HOME/zephyrproject/zephyr
EOF
    echo "Added Zephyr aliases and PATH to .bashrc"
fi

# Add to current session PATH as well
export PATH=$HOME/.local/bin:$PATH

echo ""
echo "Zephyr environment is ready!"
echo "Build the CybICS firmware with:"
echo "  cd /CybICS/software/stm32"
echo "  west build -b nucleo_g070rb"
