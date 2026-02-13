#!/bin/bash

# AgentNet Annotator - Setup Script for Ubuntu
# This script creates the conda environment and installs all dependencies
# Run with: ./setup.sh

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

# ==========================================
# 1. Ensure conda is available
# ==========================================

# Try to find and source conda from common locations
find_and_init_conda() {
    local conda_paths=(
        "${HOME}/miniconda3/etc/profile.d/conda.sh"
        "${HOME}/anaconda3/etc/profile.d/conda.sh"
        "/opt/conda/etc/profile.d/conda.sh"
        "/usr/local/miniconda3/etc/profile.d/conda.sh"
    )
    for p in "${conda_paths[@]}"; do
        if [ -f "$p" ]; then
            source "$p"
            return 0
        fi
    done
    return 1
}

if ! command -v conda &> /dev/null; then
    # conda not in PATH, try sourcing it
    if ! find_and_init_conda; then
        echo -e "${YELLOW}Conda not found. Installing Miniconda...${NC}"
        MINICONDA_INSTALLER="/tmp/Miniconda3-latest-Linux-x86_64.sh"
        wget -q --show-progress -O "$MINICONDA_INSTALLER" \
            https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
        bash "$MINICONDA_INSTALLER" -b -p "${HOME}/miniconda3"
        rm -f "$MINICONDA_INSTALLER"

        # Initialize conda for this session and future shells
        source "${HOME}/miniconda3/etc/profile.d/conda.sh"
        conda init bash 2>/dev/null || true
        echo -e "${GREEN}Miniconda installed successfully at ${HOME}/miniconda3${NC}"
    fi
else
    # conda command exists, but we still need the shell hook
    eval "$(conda shell.bash hook)"
fi

echo -e "${GREEN}Conda is ready: $(conda --version)${NC}"
echo ""

# ==========================================
# 2. Ensure Node.js is available
# ==========================================

if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing Node.js 18 via nvm...${NC}"

    # Install nvm
    export NVM_DIR="${HOME}/.nvm"
    if [ ! -d "$NVM_DIR" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    fi
    # Source nvm
    [ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

    nvm install 18
    nvm use 18
    echo -e "${GREEN}Node.js installed: $(node --version)${NC}"
else
    echo -e "${GREEN}Node.js is ready: $(node --version)${NC}"
fi

echo ""

# ==========================================
# 3. Create / reuse conda environment
# ==========================================

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

# ==========================================
# 4. Install Python dependencies
# ==========================================

echo ""
echo "Installing Python dependencies..."
pip install -r "${SCRIPT_DIR}/requirements_ubuntu.txt"

# ==========================================
# 5. Install OpenCV with GStreamer support
# ==========================================

echo ""
echo "Installing OpenCV with GStreamer support..."

# Remove any pip-installed OpenCV packages (they lack GStreamer)
python -m pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python 2>/dev/null || true

# Remove any conda-installed OpenCV packages
conda remove -y opencv libopencv py-opencv 2>/dev/null || true

# Install OpenCV with GStreamer support from conda-forge
conda install -y -c conda-forge opencv py-opencv libopencv \
  gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly

# ==========================================
# 6. Install Node.js dependencies
# ==========================================

echo ""
echo "Installing Node.js dependencies..."
cd "${SCRIPT_DIR}/agentnet-annotator"
npm install

# ==========================================
# Done
# ==========================================

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
