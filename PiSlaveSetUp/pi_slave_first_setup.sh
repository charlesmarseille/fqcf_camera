#!/bin/bash

# Add w5500 overlay to config.txt
sudo echo "dtoverlay=w5500" | sudo tee -a /boot/firmware/config.txt

sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

sudo reboot

# Get the last character of the username
LAST_CHAR=${USER: -1}

echo "The username is: $USER"
echo "The last character of the username is: $LAST_CHAR"

# Define connection name and interface
CON_NAME="eth0"
IFACE="eth0"
IP_BASE="192.168.0.10"
IP_ADDR="${IP_BASE}${LAST_CHAR}"
GATEWAY="192.168.0.1"
DNS="8.8.8.8"
echo $IP_ADDR

# Delete any existing connection using eth0 (optional safety)
sudo nmcli connection modify "Wired connection 1" ipv4.addresses "${IP_ADDR}" ipv4.gateway "${GATEWAY}" ipv4.dns "${DNS}" ipv4.method manual
sudo nmcli connection up "Wired connection 1"
sudo nmcli connection down preconfigured

sudo apt install git -y
git clone https://github.com/charlesmarseille/fqcf_camera
cd fqcf_camera/PiSlaveSetUp
chmod +x AutoSetUp.sh
sudo ./AutoSetUp.sh
