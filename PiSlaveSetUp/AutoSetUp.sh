#!/bin/bash

sudo apt-get update -y && sudo apt-get upgrade -y

# Désactiver la synchronisation automatique de l'heure
sudo timedatectl set-ntp off
#sudo apt update

#turbojpeg
sudo apt install libturbojpeg0-dev libjpeg-dev -y
sudo apt install -y cmake build-essential nasm yasm pkg-config autoconf automake libtool python3-dev python3-numpy gfortran libopenblas-dev liblapack-dev cython3 build-essential git python3-setuptools python3-wheel

cd /usr/local/src
sudo git clone https://github.com/libjpeg-turbo/libjpeg-turbo.git
cd libjpeg-turbo

sudo mkdir build && cd build

sudo cmake -G"Unix Makefiles" -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_BUILD_TYPE=Release ..
sudo make -j$(nproc)
sudo make install

cd /usr/local/src
sudo git clone https://github.com/lilohuang/PyTurboJPEG.git
cd PyTurboJPEG
sudo python3 setup.py install

echo "Installation des bibliothèques Python nécessaires..."
sudo apt install python3-picamera2 python3-ntplib python3-systemd python3-netifaces python3-opencv -y
sudo apt install libcamera-dev libcamera-apps python3-libcamera

cd ~/fqcf_camera 
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install numpy==1.24.2
python3 -c "import picamera2"
if [ $? -eq 0 ]; then
    echo "picamera2 import successful, continuing..."
else
    echo "Erreur lors de l'importation de picamera2. Arrêt du script."
    exit 1
fi


sleep 3

echo "Création du fichier de service pour la synchronisation de l'horodatage..."
PYTHON_SCRIPT_PATH=$HOME/fqcf_camera/PiSlaveSetUp/piSlaveTimeSync.py

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


echo "Lancement du script setup_ssh.sh..."
USER_HOSTNAME=$(hostname)
cd $HOME/fqcf_camera/PiSlaveSetUp
sudo chmod +x setup_ssh.sh
./setup_ssh.sh
echo "fin du script setup_ssh.sh..."
# Mettre à jour les paquets et installer rsync
sudo apt install rsync -y

echo "Création du fichier de service pour la sauvegarde continue..."
RSYNC_PATH=~/fqcf_camera/PiSlaveSetUp/rsync.sh
sudo chmod +x $RSYNC_PATH
sudo bash -c "cat > /etc/systemd/system/continuous_backup.service <<EOF
[Unit]
Description=Rsync continuous backup service
After=network.target

[Service]
ExecStart=$RSYNC_PATH
Restart=always
User=$USER_HOSTNAME
WorkingDirectory=$HOME

[Install]
WantedBy=multi-user.target
EOF"

echo "Création du fichier de service pour le script piCameraTcpSlave..."
sudo bash -c "cat > /etc/systemd/system/piSlaveTcpCamera.service <<EOF
[Unit]
Description=Service for piSlaveTcpCamera
After=network.target

[Service]
ExecStart=$HOME/fqcf_camera/venv/bin/python3 $HOME/fqcf_camera/PiSlaveSetUp/piSlaveTcpCamera.py
Restart=always
User=$USER_HOSTNAME

[Install]
WantedBy=multi-user.target
EOF"


ExecStart=$RSYNC_PATH
Restart=always
User=$USER_HOSTNAME
WorkingDirectory=$HOME

[Install]
WantedBy=multi-user.target
EOF"




# Recharger systemd et activer le service
sudo systemctl daemon-reload
sleep 5
sudo systemctl enable timestamp_sync.service
sudo systemctl enable continuous_backup.service
sudo systemctl enable piCameraTcpSlave.service
sleep 5
sudo systemctl start timestamp_sync.service
sudo systemctl start continuous_backup.service
sudo systemctl start piCameraTcpSlave.service
echo "Configuration terminée !"

echo "service continuous_backup state: "
systemctl is-active continuous_backup.service
echo "service timestamp_sync state: "
systemctl is-active timestamp_sync.service
