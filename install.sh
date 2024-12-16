#!/bin/bash -x
set -euo pipefail
# IFS=$'\n\t'

echo "Installing packages..."
apt install python3-py3exiv2 rclone python3-pip exiftool
pip install --user --break-system-packages rclone-python PyExifTool tzdata

echo "Placing autoupload.py script"
mkdir -p /usr/local/bin/
cp DCIMautoupload.py /usr/local/bin/

echo "Configuring polkit to allow plugdev users"
mkdir -p /etc/polkit-1/localauthority/50-local.d/
cp DCIMautoupload.pkla /etc/polkit-1/localauthority/50-local.d/
systemctl restart polkit.service

echo "Installing udiskie and configuring service with event hook"
apt install -y udiskie
mkdir -p /usr/local/lib/systemd/system/
cp DCIMautoupload.service /usr/local/lib/systemd/system/
systemctl daemon-reload
systemctl enable DCIMautoupload.service
systemctl restart DCIMautoupload.service

echo "rclone config needs to be done by user!"
