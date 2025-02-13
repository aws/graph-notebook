#!/bin/bash

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Get current virtual environment name
VENV_NAME=$(basename "$VIRTUAL_ENV")
if [ -z "$VENV_NAME" ]; then
    error "No virtual environment activated"
fi

log "Using virtual environment: $VENV_NAME"

# Clean previous builds
log "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
cd src/graph_notebook/widgets || error "Cannot find widgets directory"
rm -rf lib/ dist/ *.egg-info/ node_modules/ package-lock.json
rm -rf labextension/ nbextension/

log "-----------STARTING NODE SETUP-------------"

# Check node version
NODE_VERSION=$(node -v)
if [[ $NODE_VERSION != "v20.18.3" ]]; then
    error "Incorrect node version. Required: v20.18.3, Found: $NODE_VERSION"
fi

# Check npm version
NPM_VERSION=$(npm -v)
if [[ $NPM_VERSION != "10.8.2" ]]; then
    error "Incorrect npm version. Required: 10.8.2, Found: $NPM_VERSION"
fi

# Install npm dependencies
log "Installing npm dependencies..."
npm install || error "npm install failed"

# Build JavaScript/TypeScript
log "Building JavaScript/TypeScript..."
npm run build:prod || error "npm build failed"

# Verify JS build artifacts
log "Verifying JavaScript build..."
if [ ! -d "lib" ]; then
    error "lib directory not found. JavaScript build failed."
fi

if [ ! -f "lib/index.js" ]; then
    error "index.js not found in lib directory. JavaScript build incomplete."
fi

# Return to root directory
cd ../../../

log "-----------NODE SETUP DONE-------------"
log "-----------STARTING PYTHON SETUP-------------"

log "Setting up pre req python packages"
#pip install setuptools wheel twine
# Build Python wheel
log "Building Python wheel..."
python3 setup.py bdist_wheel || error "Python wheel build failed"


# Verify wheel creation
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    error "No wheel file found in dist directory"
fi

log "-----------PYTHON SETUP DONE-------------"

# Install the wheel
# Install and verify
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)
pip install "$WHEEL_FILE" --force-reinstall

log "Post whl file labextension list..."
jupyter labextension list

# Verify paths
log "Verifying installation paths..."
SITE_PACKAGES=$(pip show graph-notebook | grep Location | cut -d' ' -f2)
LABEXT_PATH="$SITE_PACKAGES/graph_notebook/widgets/labextension"
JUPYTER_PATH="/Users/$USER/$VENV_NAME/share/jupyter/labextensions/graph_notebook_widgets"
STATIC_DIR="$LABEXT_PATH/static"

# log "Verifying installation..."
# log "Site Packages: $SITE_PACKAGES"
# log "Lab Extension Path: $LABEXT_PATH"
# log "Jupyter Path: $JUPYTER_PATH"


echo "Checking installation..."

# Check if static directory exists
if [ -d "$STATIC_DIR" ]; then
    echo -e "\nFiles in static directory:"
    for file in "$STATIC_DIR"/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "  $filename"
            if [[ $filename == remoteEntry* ]]; then
                echo -e "${GREEN}✓ Found remoteEntry file${NC}"
            fi
        fi
    done
else
    echo -e "${RED}❌ Static directory not found!${NC}"
fi

# Check package.json
if [ -f "$LAB_EXT_PATH/package.json" ]; then
    echo -e "${GREEN}✓ Found package.json${NC}"
else
    echo -e "${RED}❌ package.json not found!${NC}"
fi

# Print additional debug info
echo -e "\nDebug Information:"
echo "Jupyter Path: $JUPYTER_PATH"
echo "Extension Path: $LAB_EXT_PATH"
echo -e "\nDirectory Structure:"
if [ -d "$LAB_EXT_PATH" ]; then
    ls -R "$LAB_EXT_PATH"
else
    echo -e "${RED}Extension directory not found!${NC}"
fi

# Create directories if they don't exist
# mkdir -p "$JUPYTER_PATH/static"

# # Copy files to JupyterLab extensions directory
# log "Copying files to JupyterLab extensions directory..."
# cp -r "$LABEXT_PATH"/* "$JUPYTER_PATH/" || error "Failed to copy extension files"



# Verify extension installation
if [ -d "$LABEXT_PATH" ]; then
    log "Extension files found in site-packages"
    ls -la "$LABEXT_PATH"
else
    error "Extension not found in site-packages: $LABEXT_PATH"
fi

if [ -d "$JUPYTER_PATH" ]; then
    log "Extension files found in jupyter path"
    ls -la "$JUPYTER_PATH"
else
    error "Extension not found in jupyter path: $JUPYTER_PATH"
fi

log "Calling Jupyter lab build..."

# Build JupyterLab
jupyter lab build

log "Post Jupyter lab build labextension list..."
# Final verification
jupyter labextension list

# # Build JupyterLab
# log "Building JupyterLab..."
# jupyter lab build || error "JupyterLab build failed"

log "Build and installation completed successfully!"
log "Wheel file created: $WHEEL_FILE"
