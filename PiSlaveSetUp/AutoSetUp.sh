#!/bin/bash

# Désactiver la synchronisation automatique de l'heure
sudo timedatectl set-ntp off
#sudo apt update

#turbojpeg
sudo apt install libturbojpeg0-dev libjpeg-dev -y
sudo apt install -y cmake build-essential nasm yasm pkg-config autoconf automake libtool

cd /usr/local/src
sudo git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git
cd libjpeg-turbo

#sudo mkdir build && cd build

#sudo cmake -G"Unix Makefiles" -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release ..
#sudo make -j$(nproc)
#sudo make install

cd /usr/local/src
sudo git clone https://github.com/lilohuang/PyTurboJPEG.git
cd PyTurboJPEG

sudo apt install -y python3-setuptools python3-wheel python3-dev
sudo python3 setup.py install

echo "Installation des bibliothèques Python nécessaires..."
#sudo apt update
which python3
which pip
sudo apt install python3-picamera2 python3-ntplib python3-systemd python3-netifaces python3-opencv -y

sleep 3

echo "Création du fichier de service pour la synchronisation de l'horodatage..."
PYTHON_SCRIPT_PATH=$HOME/PiSlaveSetUp/piSlaveTimeSync.py

sudo bash -c "cat > /etc/systemd/system/timestamp_sync.service <<EOF
[Unit]
Description=Service de synchronisation de l'horodatage
After=network.target

[Service]
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT_PATH
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF"

# Recharger systemd et activer le service
sudo systemctl daemon-reload
sleep 5
sudo systemctl enable timestamp_sync.service
sleep 5
sudo systemctl start timestamp_sync.service


echo "Lancement du script setup_ssh.sh..."
USER_HOSTNAME=$(hostname)
USER_HOME="/home/$USER_HOSTNAME"
cd $USER_HOME
cd fqcf_camera/PiSlaveSetUp
sudo chmod +x setup_ssh.sh
./setup_ssh.sh
echo "fin du script setup_ssh.sh..."
# Mettre à jour les paquets et installer rsync
sudo apt install rsync -y

echo "Création du fichier de service pour la sauvegarde continue..."
USER_HOSTNAME=$(hostname)
USER_HOME="/home/$USER_HOSTNAME"
RSYNC_PATH=$(readlink -f rsync.sh)

sudo chmod +x rsync.sh


sudo bash -c "cat > /etc/systemd/system/continuous_backup.service <<EOF
[Unit]
Description=Rsync continuous backup service
After=network.target

[Service]
ExecStart=$RSYNC_PATH
Restart=always
User=$USER_HOSTNAME
WorkingDirectory=$USER_HOME

[Install]
WantedBy=multi-user.target
EOF"

# Recharger systemd et activer le service de sauvegarde
sudo systemctl daemon-reload
sleep 5
sudo systemctl enable continuous_backup.service
sleep 3
sudo systemctl start continuous_backup.service
echo "Configuration terminée !"

echo "service continuous_backup state: "
systemctl is-active continuous_backup.service
echo "service timestamp_sync state: "
systemctl is-active timestamp_sync.service
