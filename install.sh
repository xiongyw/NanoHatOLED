#!/bin/bash
set -o errexit -o nounset

echo ""
echo "Welcome to NanoHatOLED Installer."
echo ""
echo "Requirements:"
echo "1) Must be connected to the internet"
echo "2) This script must be run as root user"
echo ""
echo "Steps:"
echo "Installs package dependencies:"
echo "  - python3       interactive high-level object-oriented language, python3 version"
echo "  - python3-smbus Python3 bindings for Linux SMBus access through i2c-dev"
echo "  - python3-pil   Python Imaging Library (Python3)"
echo "  - i2c-tools     This Python module allows SMBus access through the I2C /dev"
echo ""
sleep 3

echo ""
echo "Checking Internet Connectivity..."
echo "================================="
wget -q --tries=2 --timeout=100 http://www.baidu.com -O /dev/null
if [ $? -eq 0 ];then
    echo "Connected"
else
    echo "Unable to Connect, try again !!!"
    exit 0
fi

echo ""
echo "Checking User ID..."
echo "==================="
if [ $(id -u) -eq 0 ]; then
    echo "$(whoami)"
else
    echo "Please run this script as root, try 'sudo ./install.sh'."
    exit 1
fi

echo ""
echo "Checking for Updates..."
echo "======================="
sudo apt-get update --yes

echo ""
echo "Installing Dependencies"
echo "======================="
sudo apt-get install gcc python3 python3-smbus python3-pil python3-psutil i2c-tools -y
echo "Dependencies installed"

if [ ! -f /usr/bin/python3 ]; then
    echo "/usr/bin/python3 not found, exiting."
    exit 1
fi

PY3_INTERP=`readlink /usr/bin/python3`
RET=$?
if [ $? -ne 0 ]; then
    echo "No executable python3, exiting."
    exit 1
fi
REAL_PATH=$(realpath $(dirname $0))
#sed -i '/^#define.*DEBUG.*$/s/1/0/' "${REAL_PATH}/Source/daemonize.h"
sed -i "/^#define.*PYTHON3_INTERP.*$/s/\".*\"/\"${PY3_INTERP}\"/" "${REAL_PATH}/Source/daemonize.h"

echo ""
echo "Compiling with GCC ..."
echo "======================="
gcc Source/daemonize.c Source/main.c -lrt -lpthread -o NanoHatOLED
echo "Compiled NanoHatOLED"

# Disable rc.local method if it exists
if [ -f /etc/rc.local ]; then
    sed -i '\/usr\/local\/bin\/oled-start/d' /etc/rc.local
fi
if [ -f /usr/local/bin/oled-start ]; then
    rm -f /usr/local/bin/oled-start
fi

# Create systemd service
cat >/etc/systemd/system/nanohatoled.service <<EOL
[Unit]
Description=NanoHatOLED Service
After=network.target

[Service]
Type=forking
WorkingDirectory=$PWD
ExecStart=$PWD/NanoHatOLED
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable nanohatoled.service
echo "Make NanoHatOLED autostart using systemd."

echo " "
echo "Please restart to implement changes!"
echo "  _____  ______  _____ _______       _____ _______ "
echo " |  __ \ |  ____|/ ____|__   __|/\   |  __ \__   __|"
echo " | |__) || |__  | (___    | |  /  \  | |__) | | |   "
echo " |  _  / |  __|  \___ \   | | / /\ \ |  _  /  | |   "
echo " | | \ \ | |____ ____) |  | |/ ____ \| | \ \  | |   "
echo " |_|  \_\|______|_____/   |_/_/    \_\_|  \_\ |_|   "
echo " "
echo "To finish changes, we will reboot the Pi."
echo "Pi must reboot for changes and updates to take effect."
echo "If you need to abort the reboot, press Ctrl+C.  Otherwise, reboot!"
echo "Rebooting in 5 seconds!"
sleep 1
echo "Rebooting in 4 seconds!"
sleep 1
echo "Rebooting in 3 seconds!"
sleep 1
echo "Rebooting in 2 seconds!"
sleep 1
echo "Rebooting in 1 seconds!"
sleep 1
echo "Rebooting now!  "
sleep 1
sudo reboot

