#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting installation script for WhatsApp Sender..."
APP_DIR="/opt/whatsapp-sender" # Define app directory variable
VENV_DIR="$APP_DIR/venv"

# 1. Update package lists
echo "Updating package lists..."
sudo apt update

# 2. Install necessary system packages (python3, python3-pip, python3-venv, xvfb, wget, ca-certificates, jq)
echo "Installing system packages (python3, python3-pip, python3-venv, xvfb, wget, ca-certificates, jq)..."
sudo apt install -y python3 python3-pip python3-venv xvfb wget ca-certificates jq # Added jq

# 3. Install Firefox ESR from Mozilla tarball
FIREFOX_ESR_URL="https://download.mozilla.org/?product=firefox-esr-latest&os=linux64&lang=en-US"
FIREFOX_TAR_PATH="/tmp/firefox-esr.tar.bz2"
FIREFOX_INSTALL_DIR="/opt/firefox_esr"

echo "Downloading Firefox ESR from Mozilla..."
sudo wget -O "$FIREFOX_TAR_PATH" "$FIREFOX_ESR_URL"   -U "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

echo "Extracting Firefox ESR to $FIREFOX_INSTALL_DIR..."
sudo rm -rf "$FIREFOX_INSTALL_DIR" 
sudo mkdir -p "$FIREFOX_INSTALL_DIR"
sudo tar -xjf "$FIREFOX_TAR_PATH" -C "$FIREFOX_INSTALL_DIR" --strip-components=1
rm "$FIREFOX_TAR_PATH"

echo "Creating symbolic link for Firefox ESR..."
sudo ln -sf "$FIREFOX_INSTALL_DIR/firefox" /usr/local/bin/firefox
echo "Firefox ESR installed successfully."

# 4. Install geckodriver 
echo "Fetching latest geckodriver version using GitHub API and jq..."
# Use -S for errors with wget, -s for silent for jq, ensure output is clean for variable assignment
LATEST_GECKODRIVER_VERSION=$(wget -S -q -O - "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | jq -r '.tag_name // empty')

if [ -z "$LATEST_GECKODRIVER_VERSION" ]; then
    echo "ERROR: Failed to fetch latest geckodriver version. GitHub API might be rate-limiting or jq parsing failed."
    echo "Please check network or try again later. As a fallback, you can manually set LATEST_GECKODRIVER_VERSION in the script."
    # Example of manual fallback: LATEST_GECKODRIVER_VERSION="v0.34.0" 
    exit 1
fi
echo "Latest geckodriver version is $LATEST_GECKODRIVER_VERSION"

GECKODRIVER_DOWNLOAD_URL="https://github.com/mozilla/geckodriver/releases/download/$LATEST_GECKODRIVER_VERSION/geckodriver-$LATEST_GECKODRIVER_VERSION-linux64.tar.gz"
echo "Downloading geckodriver from $GECKODRIVER_DOWNLOAD_URL..."
wget -q -O /tmp/geckodriver.tar.gz "$GECKODRIVER_DOWNLOAD_URL"

echo "Installing geckodriver..."
sudo tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin
rm /tmp/geckodriver.tar.gz
sudo chmod +x /usr/local/bin/geckodriver
echo "Geckodriver installed to /usr/local/bin/geckodriver"

# 5. Create application base directory
echo "Ensuring application base directory $APP_DIR exists..."
sudo mkdir -p $APP_DIR

# 6. Create Python virtual environment
echo "Creating Python virtual environment at $VENV_DIR..."
sudo rm -rf "$VENV_DIR" 
sudo python3 -m venv "$VENV_DIR"
echo "Virtual environment created."

# 7. Install Python dependencies into the virtual environment
echo "Installing Python dependencies from requirements.txt into $VENV_DIR..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
else
    echo "ERROR: requirements.txt not found in $APP_DIR. Please ensure it exists there."
    exit 1
fi
echo "Python dependencies installed in virtual environment."

# 8. Create application sub-directories
echo "Creating application sub-directories under $APP_DIR/..."
sudo mkdir -p "$APP_DIR/app"
sudo mkdir -p "$APP_DIR/uploads"
sudo mkdir -p "$APP_DIR/sessions"
sudo mkdir -p "$APP_DIR/logs"
    
echo "Installation script completed successfully."
echo "Next steps:"
echo "1. Ensure your Flask application files are in $APP_DIR/app/."
echo "2. Reload systemd daemon and restart the service: sudo systemctl daemon-reload && sudo systemctl restart whatsapp-sender.service"
echo "3. Check service status: sudo systemctl status whatsapp-sender.service"
