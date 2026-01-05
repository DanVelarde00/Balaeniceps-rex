#!/bin/bash

set -e  # Exit on error
set -o pipefail  # Catch piped command errors

USER=$(whoami)
PROJECT_DIR="/home/$USER/peregrine"
YOLO_MODEL_URL="https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
LOG_FILE="$PROJECT_DIR/install_log.txt"

echo "📜 Logging to $LOG_FILE"
mkdir -p "$PROJECT_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

### 1. System Update ###
echo "🔧 Updating system..."
sudo apt update && sudo apt upgrade -y

### 2. Install System Dependencies ###
echo "📦 Installing system dependencies..."
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    python3-gst-1.0 \
    python3-picamera2 \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    python3-venv \
    git \
    cmake \
    ninja-build \
    protobuf-compiler \
    libprotobuf-dev \
    libopencv-dev \
    wget

### 3. Clone Peregrine Repo ###
echo "📁 Cloning Peregrine repository..."
rm -rf "$PROJECT_DIR"
git clone https://dan.a.velarde.mil:RioxiBMsY3YWv8qbBmdY@sync.git.mil/ai2c/robotics-and-autonomous-systems/peregrine-black.git "$PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "❌ requirements.txt not found after clone. Possible clone failure."
    exit 1
fi

### 4. Python Environment Setup ###
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

### 5. Download YOLOv8 and Export NCNN ###
echo "📦 Downloading YOLOv8 model..."
mkdir -p "$PROJECT_DIR/models"
cd "$PROJECT_DIR/models"
wget -nc "$YOLO_MODEL_URL"
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='ncnn', imgsz=480)"

### 6. Set Peregrine to Run on Startup ###
echo "🔧 Configuring rc.local to run Peregrine on boot..."
sudo tee /etc/rc.local > /dev/null <<EOF
#!/bin/sh -e
/usr/bin/env
cd $PROJECT_DIR || exit 1
. .venv/bin/activate
python peregrine_test.py raspi_default &
exit 0
EOF
sudo chmod +x /etc/rc.local

### 7. Composite Video Resolution Fix ###
echo "🖥️ Setting composite video resolution..."
sudo sed -i 's/\(rootwait\)/\1 video=Composite-1:720x480@60ie/' /boot/firmware/cmdline.txt

### 8. Disable Bluetooth ###
echo "📡 Disabling Bluetooth..."
if ! grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt; then
    echo -e "\n# Disable bluetooth\ndtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
fi

### Done ###
echo "✅ Peregrine installation complete. Please reboot manually or run: sudo reboot"