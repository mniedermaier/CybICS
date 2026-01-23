#!/bin/bash
set -e

# Change to the app directory (parent of scripts/)
cd "$(dirname "$0")/.."

# Build the STM32 application
west build -b nucleo_g070rb
