#!/bin/bash

# AgentNet Annotator - Setup Script for Ubuntu
# This script creates the conda environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "AgentNet Annotator Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: conda is not installed or not in PATH${NC}"
    echo "Please install Miniconda or Anaconda first:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js (v18+) first:"
    echo "  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    exit 1
fi

echo -e "${GREEN}Prerequisites check passed!${NC}"
echo ""

# Initialize conda for bash
echo "Initializing conda..."
eval "$(conda shell.bash hook)"

# Check if agentnet environment already exists
if conda env list | grep -q "^agentnet "; then
    echo -e "${YELLOW}Conda environment 'agentnet' already exists.${NC}"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda deactivate 2>/dev/null || true
        conda env remove -n agentnet -y
    else
        echo "Using existing environment..."
    fi
fi

# Create conda environment if it doesn't exist
if ! conda env list | grep -q "^agentnet "; then
    echo ""
    echo "Creating conda environment 'agentnet' with Python 3.11..."
    conda create -n agentnet python=3.11 -y
fi

# Activate the environment
echo ""
echo "Activating conda environment..."
conda activate agentnet

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r "${SCRIPT_DIR}/requirements_ubuntu.txt"

# Install Node.js dependencies
echo ""
echo "Installing Node.js dependencies..."
cd "${SCRIPT_DIR}/agentnet-annotator"
npm install

echo ""
echo -e "${GREEN}=========================================="
echo "Setup completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Copy .env.example to .env and fill in your credentials:"
echo "   cp .env.example .env"
echo "   nano .env  # or use your preferred editor"
echo ""
echo "2. Install OBS Studio (required for screen recording):"
echo "   sudo apt install obs-studio"
echo "   See OBS_SETUP.md for configuration instructions"
echo ""
echo "3. Run the application:"
echo "   ./start.sh"
echo ""
echo -e "${YELLOW}Note: This application requires a GUI (X11/Wayland display).${NC}"
echo "If running on a headless server, you'll need X11 forwarding or VNC."
