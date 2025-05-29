#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting installation script for WhatsApp Sender..."
APP_DIR="/opt/whatsapp-sender" # Define app directory variable
VENV_DIR="$APP_DIR/venv"

# 1. Update package lists
echo "Updating package lists..."
sudo apt update

# 2. Install necessary system packages (python3, python3-pip, python3-venv, xvfb, wget, ca-certificates)
echo "Installing system packages (python3, python3-pip, python3-venv, xvfb, wget, ca-certificates)..."
sudo apt install -y python3 python3-pip python3-venv xvfb wget ca-certificates

# 3. Install Firefox ESR from Mozilla tarball (This part should remain as previously corrected)
FIREFOX_ESR_URL="https://download.mozilla.org/?product=firefox-esr-latest&os=linux64&lang=en-US"
FIREFOX_TAR_PATH="/tmp/firefox-esr.tar.bz2"
FIREFOX_INSTALL_DIR="/opt/firefox_esr"

echo "Downloading Firefox ESR from Mozilla..."
sudo wget -O "$FIREFOX_TAR_PATH" "$FIREFOX_ESR_URL"   -U "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

echo "Extracting Firefox ESR to $FIREFOX_INSTALL_DIR..."
sudo mkdir -p "$FIREFOX_INSTALL_DIR"
sudo tar -xjf "$FIREFOX_TAR_PATH" -C "$FIREFOX_INSTALL_DIR" --strip-components=1
rm "$FIREFOX_TAR_PATH"

echo "Creating symbolic link for Firefox ESR..."
sudo ln -sf "$FIREFOX_INSTALL_DIR/firefox" /usr/local/bin/firefox
echo "Firefox ESR installed successfully."

# 4. Install geckodriver (This part should remain as previously corrected)
LATEST_GECKODRIVER_VERSION=$(wget -q -O - "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*//')
echo "Latest geckodriver version is $LATEST_GECKODRIVER_VERSION"

GECKODRIVER_DOWNLOAD_URL="https://github.com/mozilla/geckodriver/releases/download/$LATEST_GECKODRIVER_VERSION/geckodriver-$LATEST_GECKODRIVER_VERSION-linux64.tar.gz"
echo "Downloading geckodriver from $GECKODRIVER_DOWNLOAD_URL..."
wget -q -O /tmp/geckodriver.tar.gz "$GECKODRIVER_DOWNLOAD_URL"

echo "Installing geckodriver..."
sudo tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin
rm /tmp/geckodriver.tar.gz
sudo chmod +x /usr/local/bin/geckodriver
echo "Geckodriver installed to /usr/local/bin/geckodriver"

# 5. Create application directories (ensure this is done before venv creation in APP_DIR)
echo "Creating application base directory $APP_DIR if it doesn't exist..."
sudo mkdir -p $APP_DIR 
# The following subdirectories are created later, this just ensures APP_DIR exists for venv.

# 6. Create Python virtual environment
echo "Creating Python virtual environment at $VENV_DIR..."
sudo python3 -m venv "$VENV_DIR"
echo "Virtual environment created."

# 7. Install Python dependencies into the virtual environment
echo "Installing Python dependencies from requirements.txt into $VENV_DIR..."
if [ -f "$APP_DIR/requirements.txt" ]; then # Look for requirements.txt in APP_DIR
    sudo "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
else
    echo "ERROR: requirements.txt not found in $APP_DIR. Make sure it's in that directory."
    # Attempt to find it in current directory as a fallback, assuming script is run from APP_DIR
    if [ -f "./requirements.txt" ]; then
        echo "Found requirements.txt in current directory. Installing from here..."
        sudo "$VENV_DIR/bin/pip" install -r "./requirements.txt"
    else
        echo "ERROR: requirements.txt also not found in current directory. Please ensure it exists."
        exit 1
    fi
fi
echo "Python dependencies installed in virtual environment."

# 8. Create application sub-directories (if not already handled by git clone)
echo "Creating application sub-directories under $APP_DIR/..."
sudo mkdir -p "$APP_DIR/app"
sudo mkdir -p "$APP_DIR/uploads"
sudo mkdir -p "$APP_DIR/sessions"
sudo mkdir -p "$APP_DIR/logs"

# Set ownership of the app directory to the user who will run the app (e.g., 'ubuntu' or 'www-data')
# This is important for Flask to be able to write to uploads, sessions, logs if not running as root
# For now, let's assume the systemd service will run as root, or this needs user input.
# If running systemd as root, sudo for pip install is fine. If systemd runs as non-root,
# then venv and app dir should be owned by that user.
# Example: sudo chown -R youruser:yourgroup $APP_DIR

echo "Installation script completed successfully."
echo "Next steps:"
echo "1. Ensure your Flask application is in $APP_DIR/ (e.g., $APP_DIR/app/app.py)."
echo "2. Update whatsapp-sender.service to use python from $VENV_DIR/bin/python3."
echo "3. Reload systemd daemon and restart the service."
