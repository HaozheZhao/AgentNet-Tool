#!/bin/bash

# AgentNet Annotator - Start Script
# This script starts the AgentNet Annotator application

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment variables from .env file if it exists
if [ -f "${SCRIPT_DIR}/.env" ]; then
    echo "Loading environment variables from .env..."
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    echo "Cloud upload features may not work without OSS credentials."
    echo "Copy .env.example to .env and configure your credentials."
    echo ""
fi

# Initialize conda - try common locations using $HOME (works for any user)
CONDA_PATHS=(
    "${CONDA_PATH}/etc/profile.d/conda.sh"
    "${HOME}/miniconda3/etc/profile.d/conda.sh"
    "${HOME}/anaconda3/etc/profile.d/conda.sh"
    "/opt/conda/etc/profile.d/conda.sh"
    "/usr/local/miniconda3/etc/profile.d/conda.sh"
)

CONDA_INIT=""
for path in "${CONDA_PATHS[@]}"; do
    if [ -f "$path" ]; then
        CONDA_INIT="$path"
        break
    fi
done

if [ -z "$CONDA_INIT" ]; then
    echo -e "${RED}Error: Could not find conda installation.${NC}"
    echo "Please run ./setup.sh first, or set CONDA_PATH in your .env file."
    exit 1
fi

source "$CONDA_INIT"

# Activate the agentnet environment
if ! conda activate agentnet 2>/dev/null; then
    echo -e "${RED}Error: Conda environment 'agentnet' not found.${NC}"
    echo "Please run ./setup.sh first to create the environment."
    exit 1
fi

echo -e "${GREEN}Starting AgentNet Annotator...${NC}"
echo ""

# Change to the agentnet-annotator directory and start the app
cd "${SCRIPT_DIR}/agentnet-annotator"
npm start
