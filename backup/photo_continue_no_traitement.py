import os
import time
from datetime import datetime
from picamera2 import Picamera2
import numpy as np
#import cv2
import ctypes
from threading import Thread
import faulthandler

picam2 = Picamera2()
	
# Configuration initiale avec auto-réglages
config = picam2.create_still_configuration(buffer_count = 1, main={"format": "RGB888", "size": (4608, 2592)},
														controls={"AfMode": 2, "LensPosition":1.1, "AwbEnable": False,"AeEnable": False, "NoiseReductionMode": 0, "AnalogueGain": 15, "ExposureTime":1200})
picam2.configure(config)

print(config)
#serialized_config = serialize_config(config)
picam2.start()

# Dossier de destination
dossier_destination = "/home/pi1/"
os.makedirs(dossier_destination, exist_ok=True)

id = 0  # Identifiant pour les fichiers

liste_noms_images = []

# Vérifie si le dossier existe, sinon le crée
if not os.path.exists(dossier_destination):
	os.makedirs(dossier_destination)

width=4608
height=2592

def save_image(nom_fichier, buffer):
	#ajouter dans la liste le nom de l'image
	liste_noms_images.append(nom_fichier)

while id<200:
	# Capture et enregistre la photo
	the_id=id
	id+=1
	nom_fichier = os.path.join(dossier_destination, "pi1_"+ str(the_id) + "_" +datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]+ ".jpg") #date format YYYYMMDD_HHMMSSmmm
	request = picam2.capture_request()
	buffer = request.make_buffer('main')
	request.release()
	t = Thread(target=save_image, args=(nom_fichier, buffer))
	t.start()
	print(f"{id}")

with open(os.path.join(dossier_destination, "liste_images.txt"), "w") as f:
	f.write("\n".join(liste_noms_images))