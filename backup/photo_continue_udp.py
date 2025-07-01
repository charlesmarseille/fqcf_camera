import os
import time
from datetime import datetime
from picamera2 import Picamera2
import numpy as np
#import cv2
import ctypes
from threading import Thread
import socket

PORT = 12344  # Port d'envoi des requête
IP = "192.168.0.100"  # Adresse de broadcast pour envoyer à tous les RPi
HEADER = b"Envoi_Photo"  

picam2 = Picamera2()
	
# Configuration initiale avec auto-réglages
config = picam2.create_still_configuration(buffer_count = 1, main={"format": "RGB888", "size": (4608, 2592)},
														controls={"AfMode": 2, "LensPosition":1.1, "AwbEnable": False,"AeEnable": False, "NoiseReductionMode": 0, "AnalogueGain": 15, "ExposureTime":1200})
picam2.configure(config)

print(config)
#serialized_config = serialize_config(config)
picam2.start()

# Dossier de destination
dossier_destination = "/home/pi1/photo/"
os.makedirs(dossier_destination, exist_ok=True)

id = 0  # Identifiant pour les fichiers

# Vérifie si le dossier existe, sinon le crée
if not os.path.exists(dossier_destination):
	os.makedirs(dossier_destination)

width=4608
height=2592

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def save_image(nom_fichier, buffer):
	the_buffer = buffer.tobytes()  # Convertir en bytes
	metadata = f"{nom_fichier}:{buffer.shape}:{buffer.dtype}".encode()  # Métadonnées
    
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP au lieu d'UDP
	sock.connect((IP, PORT))

    # Envoyer la taille des métadonnées et du buffer
	sock.sendall(len(metadata).to_bytes(4, "big"))  # Envoyer la taille des métadonnées
	sock.sendall(metadata)  # Envoyer les métadonnées
	sock.sendall(len(the_buffer).to_bytes(4, "big"))  # Taille du buffer
	sock.sendall(the_buffer)  # Envoyer le buffer

	sock.close()
	print("Image envoyée avec succès via TCP.")


while True:
	# Capture et enregistre la photo
	the_id=id
	id+=1
	nom_fichier = os.path.join(dossier_destination, "pi1_"+ str(the_id) + "_" +datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]+ ".jpg") #date format YYYYMMDD_HHMMSSmmm
	request = picam2.capture_request()
	buffer = request.make_buffer('main')
	print(len(buffer)) 
	print(buffer.shape)
	print(type(buffer))
	print(buffer)
	request.release()
	t = Thread(target=save_image, args=(nom_fichier, buffer))
	t.start()
	print(f"{id}")