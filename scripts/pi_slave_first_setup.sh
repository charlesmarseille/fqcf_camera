#!/bin/bash

# Add w5500 overlay to config.txt
echo "dtoverlay=w5500" | sudo tee -a /boot/firmware/config.txt

raspi-config nonint do_spi 0
raspi-config nonint do_i2c 0

# Get the last character of the username
LAST_CHAR=${USERNAME: -1}

echo "The username is: $USERNAME"
echo "The last character of the username is: $LAST_CHAR"

# Define connection name and interface
CON_NAME="eth0"
IFACE="eth0"
IP_BASE="192.168.0.10"
IP_ADDR="${IP_BASE}${LAST_CHAR}/24"
GATEWAY="192.168.0.1"
DNS="8.8.8.8"

# Delete any existing connection using eth0 (optional safety)
nmcli con delete "$CON_NAME" 2>/dev/null
nmcli con add type ethernet ifname "$IFACE" con-name "$CON_NAME" ipv4.method manual ipv4.addresses "$IP_ADDR" ipv4.gateway "$GATEWAY" ipv4.dns "$DNS" ipv6.method ignore

# Bring up the connection
nmcli con up "$CON_NAME"

apt install git
git clone https://github.com/charlesmarseille/fqcf_camera
cd fqcf_camera/PiSlaveSetUp
chmod +x AutoSetUp.sh
./AutoSetUp.sh