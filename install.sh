#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting installation script for WhatsApp Sender..."

# 1. Update package lists
echo "Updating package lists..."
sudo apt update

# 2. Install necessary system packages
echo "Installing system packages (python3, python3-pip, firefox, xvfb)..."
sudo apt install -y python3 python3-pip firefox xvfb wget

# Check if geckodriver needs to be manually installed
# Get the latest geckodriver version
LATEST_GECKODRIVER_VERSION=$(wget -q -O - "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*//')
echo "Latest geckodriver version is $LATEST_GECKODRIVER_VERSION"

# Download and install geckodriver
GECKODRIVER_DOWNLOAD_URL="https://github.com/mozilla/geckodriver/releases/download/$LATEST_GECKODRIVER_VERSION/geckodriver-$LATEST_GECKODRIVER_VERSION-linux64.tar.gz"
echo "Downloading geckodriver from $GECKODRIVER_DOWNLOAD_URL..."
wget -q -O /tmp/geckodriver.tar.gz "$GECKODRIVER_DOWNLOAD_URL"

echo "Installing geckodriver..."
sudo tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin
rm /tmp/geckodriver.tar.gz
sudo chmod +x /usr/local/bin/geckodriver
echo "Geckodriver installed to /usr/local/bin/geckodriver"


# 3. Install Python dependencies
# Assuming requirements.txt is in the same directory as the script,
# which will be /opt/whatsapp-sender/ when deploying.
echo "Installing Python dependencies from requirements.txt..."
if [ -f ./requirements.txt ]; then
    sudo pip3 install -r ./requirements.txt
else
    echo "ERROR: requirements.txt not found. Make sure it's in the current directory."
    exit 1
fi

# 4. Create application directories
# These directories will be under /opt/whatsapp-sender
# The application code (app/*) itself should be copied here manually or by a deployment script.
echo "Creating application directories under /opt/whatsapp-sender/..."
sudo mkdir -p /opt/whatsapp-sender/app
sudo mkdir -p /opt/whatsapp-sender/uploads
sudo mkdir -p /opt/whatsapp-sender/sessions
sudo mkdir -p /opt/whatsapp-sender/logs

# Set permissions if needed (e.g., if running Flask under a non-root user)
# For now, assuming Flask will run with sufficient permissions or as current user who runs it.
# sudo chown -R youruser:yourgroup /opt/whatsapp-sender # Example

echo "Installation script completed successfully."
echo "Next steps:"
echo "1. Copy your Flask application (app/*, app.py, etc.) to /opt/whatsapp-sender/"
echo "2. Ensure your app/app.py refers to paths like 'uploads/' relative to /opt/whatsapp-sender/ (e.g. UPLOAD_FOLDER = 'uploads')"
echo "3. Set up a systemd service to run the application (e.g., using xvfb-run)."
