import socket
import os
import sys
from datetime import datetime
from systemd import daemon
from picamera2 import Picamera2
import json

# Configuration
pi_number = os.uname().nodename[-1]
PORT = 12344  # Port d'écoute
BUFFER_SIZE = 1024  # Taille du buffer de réception
INTERFACE = "eth0"  # Interface réseau spécifique
HEADER = "Photo" 
CONFIG_PORT = 5000  # Port d'écoute pour la configuration

def receive_Picture_Request():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))
    sock.listen(1)  # Listen for incoming TCP connections

    print(f"Waiting for picture request on port {PORT}...")
    picam2 = Picamera2()
    # picam2.configure(picam2.create_still_configuration(main={"format": "RGB888", "size": (4608,2592)}, controls={"AwbEnable": False, "Brightness": 0.0, "Contrast": 0.0, "Saturation": 0.0,"Sharpness": 0.0, "ExposureTime": 1000, "AnalogueGain": 1.0, "ColourGains": (1.0,1.0), "LensPosition": 0.0, "AfMode":0,"NoiseReductionMode": 0, "ScalerCrop": (0,0,4608,2592) } ))
    picam2.configure(picam2.create_still_configuration(main={"format": "RGB888", "size": (4608,2592)}))

    # Dossier de destination
    dossier_destination = "photo"
    os.makedirs(dossier_destination, exist_ok=True)

    # Démarrage de la caméra
    picam2.start()

    while True:
        try:
            print("waiting for connection...")
            conn, addr = sock.accept()
            with conn:
                data = conn.recv(BUFFER_SIZE)
                message = data.decode().strip()
                print(f"Packet received from {addr}: {message}")
                if message.startswith(HEADER):
                    id = int(message.split("Photo:")[1])
                    nom_fichier = os.path.join(dossier_destination, f"pi{pi_number}_{id}_" + datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3] + ".jpg")  # date format YYYYMMDD_HHMMSSmmm
                    picam2.capture_file(nom_fichier)
                else:
                    print(f"Packet ignored, invalid format: {message}")
        except Exception as e:
            print(f"Error receiving packet: {e}")

if __name__ == "__main__":
    receive_Picture_Request()
