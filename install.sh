#!/bin/bash -e

apt_updated=0
function ensure_updated() {
  if [ "$apt_updated" -eq 0 ]; then
    echo "Updating package index..."
    sudo apt update
    apt_updated=1
  fi
}

function ensure_cmd() {
  local cmd=$1
  local pkg=$2
  if ! command -v "$cmd" &>/dev/null; then
    echo "Installing $pkg for $cmd..."
    ensure_updated
    sudo apt install -y "$pkg"
  else
    echo "$cmd is already installed"
  fi
}

ensure_cmd python3 python3
ensure_cmd pip3 python3-pip
ensure_cmd python3-venv python3-venv
ensure_cmd ffmpeg ffmpeg
ensure_cmd zip zip
ensure_cmd aws awscli

INSTALL_DIR=/opt/ttv_stream_rec
VENV_DIR="$INSTALL_DIR/.venv"
sudo mkdir -p "$INSTALL_DIR"
sudo chown "$USER":"$USER" "$INSTALL_DIR"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

(
  source "$VENV_DIR/bin/activate"
  pip3 install streamlink python-dotenv requests boto3
)

curl -fsSL https://raw.githubusercontent.com/Renne1002/ttv_stream_rec/main/main.py -o "$INSTALL_DIR/main.py"
curl -fsSL https://raw.githubusercontent.com/Renne1002/ttv_stream_rec/main/sample.service -o "$INSTALL_DIR/sample.service"
curl -fsSL https://raw.githubusercontent.com/Renne1002/ttv_stream_rec/main/sample.env -o "$INSTALL_DIR/.env"
