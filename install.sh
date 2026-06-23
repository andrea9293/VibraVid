#!/bin/bash
set -e

REPO="andrea9293/VibraVid"
BINARY_NAME="vibravid-agent"
INSTALL_DIR="${HOME}/.local/bin"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Map OS/arch to GitHub asset name (must end with -agent)
case "$OS" in
    linux) ASSET_PATTERN="linux.*${ARCH}-agent" ;;
    darwin) ASSET_PATTERN="mac.*${ARCH}-agent" ;;
    mingw*|msys*|cygwin*) ASSET_PATTERN="win.*${ARCH}-agent\.exe$"; BINARY_NAME+=".exe" ;;
    *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Download latest release
echo "Downloading latest release from ${REPO}..."
LATEST_URL=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | \
    grep "browser_download_url" | \
    grep -E "$ASSET_PATTERN" | \
    head -1 | \
    cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
    echo "Error: no asset found for ${OS}/${ARCH}"
    exit 1
fi

curl -L "$LATEST_URL" -o "${INSTALL_DIR}/${BINARY_NAME}"
chmod +x "${INSTALL_DIR}/${BINARY_NAME}"

# Verify installation
if ! command -v "$BINARY_NAME" &> /dev/null; then
    echo "Warning: ${INSTALL_DIR} is not in PATH"
    echo "Add to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
fi

echo "✓ ${BINARY_NAME} installed successfully in ${INSTALL_DIR}/${BINARY_NAME}"
echo "Run '${BINARY_NAME} --version' to verify"
