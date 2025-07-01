import socket
import os
import sys
from datetime import datetime
from systemd import daemon
from picamera2 import Picamera2
import json
import time

# Configuration
PORT = 12344  # Port d'écoute
BUFFER_SIZE = 99999  # Taille du buffer de réception
INTERFACE = "eth0"  # Interface réseau spécifique
HEADER = "Photo" 
CONFIG_PORT = 5000  # Port d'écoute pour la configuration



def receive_Picture_Request():
    picam2 = Picamera2()
    
    # Configuration initiale avec auto-réglages
    picam2.configure(picam2.create_still_configuration(buffer_count = 2, main={"format": "RGB888", "size": (640, 480)},
                                                        controls={"AfMode": 0, "LensPosition": 1.2, "NoiseReductionMode": 0})) #autofocus a off et focus environ 90cm
    picam2.start()
    time.sleep(3)
    
    # Récupérer les paramètres après auto-ajustement
    metadata = picam2.capture_metadata()
    picam2.stop()
    # Désactiver les réglages automatiques et appliquer les valeurs enregistrées
    config_verrouillee = {
        "AwbEnable": False,
        "AeEnable": False,
        "ExposureTime": metadata.get("ExposureTime", 1000),
        "AnalogueGain": metadata.get("AnalogueGain", 1.0),
        "ColourGains": metadata.get("ColourGains", (1.0, 1.0)),
    }
    
    config = picam2.create_still_configuration(buffer_count = 2, main={"format": "RGB888", "size": (640, 480)}, #tester queue = False
                                                        controls={**config_verrouillee, "AfMode": 0, "LensPosition": 1.2})#"NoiseReductionMode": 0
    picam2.configure(config)


    #serialized_config = serialize_config(config)
    picam2.start()

    # Dossier de destination
    dossier_destination = "/home/pi3/photo/"
    os.makedirs(dossier_destination, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))  # Écoute sur toutes les interfaces pour voir tous les paquets

    # Démarrage de la caméra
    picam2.start()

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode().strip()
            print(f"Paquet reçu de {addr}: {message}")
            if message.startswith(HEADER):
                id = message.split("Photo:")[1]
                nom_fichier = os.path.join(dossier_destination, "pi3_"+ str(id) + "_" +datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]+ ".jpg") #date format YYYYMMDD_HHMMSSmmm
                request = picam2.capture_request(flush=True)
                request.save("main", nom_fichier)
                request.release()
            elif message.startswith("END"):
                print("c'est la fin!")
                sys.exit()
            else:
                print("Paquet ignoré, format invalide.")
        except Exception as e:
            print(f"Erreur lors de la réception du paquet: {e}")

if __name__ == "__main__":
    receive_Picture_Request()
