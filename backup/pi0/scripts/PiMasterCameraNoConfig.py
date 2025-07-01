import time
import socket
import ntplib
import os
import json
import sys
from datetime import datetime
from picamera2 import Picamera2



# Configuration
PORT = 12344  # Port d'envoi des requête
BROADCAST_IP = "255.255.255.255"  # Adresse de broadcast pour envoyer à tous les RPi
HEADER = "Photo"  # Entête pour identifier les paquets
ENDHEADER = "END"
config_send_sucessful = True


def broadcast_Picture():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    picam2 = Picamera2()
    
    config = picam2.create_still_configuration(buffer_count = 2, main={"format": "RGB888", "size": (4608, 2592)},
                                                        controls={"AfMode": 1, "AwbEnable": False,"AeEnable": False, "NoiseReductionMode": 0, "AnalogueGain": 25, "ExposureTime": 800})
    picam2.configure(config)

    print(config)

    # Dossier de destination
    dossier_destination = "/mnt/ssd/backup/0/"
    os.makedirs(dossier_destination, exist_ok=True)

    picam2.start()
    
    time.sleep(5)
    id = 0
    try:
        while True: # si la config a bien été envoyé et décodé, prend des photos, sinon le script arrête son exécution
            message = f"{HEADER}:{id}".encode() #id
            #print("envoi")
            sock.sendto(message, (BROADCAST_IP, PORT))
            #print("nom")
            nom_fichier = os.path.join(dossier_destination, "pi0_"+ str(id) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3] + ".jpg") #date format YYYYMMDD_HHMMSSmmm
            #print("capture")
            request = picam2.capture_request(flush=True)
            #print("save")
            request.save("main", nom_fichier)
            #print("release")
            request.release()
            print(id)
            id +=1
            time.sleep(0.1)
    except KeyboardInterrupt:
        message = f"{ENDHEADER}".encode()
        sock.sendto(message, (BROADCAST_IP, PORT))
        sys.exit()


if __name__ == "__main__":
    broadcast_Picture()