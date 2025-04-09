#!/usr/bin/env bash

# Define colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper function to print colored status
info() { echo -e "${CYAN}==>${NC} $1"; }
success() { echo -e "${GREEN}✔${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✖${NC} $1"; }

# Step 1: Check if Python is installed
info "Checking for Python..."

if command -v python3 &>/dev/null; then
    success "Python found as 'python3'"
    PY=python3
elif command -v python &>/dev/null; then
    success "Python found as 'python'"
    PY=python
else
    error "Python is not installed. Please install Python and try again."
    exit 1
fi

# Step 2: Create virtual environment and activate it
info "Creating virtual environment..."
$PY -m venv .venv

if [ ! -f ".venv/bin/activate" ]; then
    error "Virtual environment activation script not found. Something went wrong."
    exit 1
fi

info "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate
success "Virtual environment activated."

# Step 3: Install Poetry and dependencies
info "Installing Poetry..."
pip install poetry

info "Installing project dependencies with Poetry..."
poetry install

success "Setup complete!"
