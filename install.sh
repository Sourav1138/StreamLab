#!/bin/bash

echo "🚀 Starting StreamLab Installation for Termux..."

# 1. Update and Upgrade System
echo "🔄 Updating system packages..."
pkg update && pkg upgrade -y

# 2. Install Core Packages
echo "📦 Installing git, python, and ffmpeg..."
pkg install git python ffmpeg -y

# 3. Setup Storage Access
echo "📁 Requesting storage access..."
termux-setup-storage
echo "⚠️ Please tap 'Allow' on the popup window if it appears."

# 4. Setup Python Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# 5. Install Python Dependencies
echo "🛠 Installing Flask, Requests, and yt-dlp..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Installation Complete!"
echo "------------------------------------------------"
echo "To start the server, run:"
echo "source venv/bin/activate"
echo "python app.py"
echo "------------------------------------------------"
EOF
