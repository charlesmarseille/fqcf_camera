import time
import socket
import ntplib
import os
import json
import sys
from datetime import datetime
from libcamera import controls
from picamera2 import Picamera2


def broadcast_Picture():
	picam2 = Picamera2()

	config = picam2.create_still_configuration()
	picam2.configure(config)

	print(config)

	picam2.start()

	gain=100
	exposure=500
    # Dossier de destination
	dossier_destination = "/home/pi0/test_qr"
	os.makedirs(dossier_destination, exist_ok=True)
	picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	picam2.set_controls({"ExposureTime": gain, "AnalogueGain": exposure})
	time.sleep(5)
	id = 0
	while True:
		action = input(" Appuyez sur 'Entrée' pour prendre une photo ou 'q' + Entrée pour quitter : ")

		if action.lower() == "q":

			print(" Arrêt du script.")
			break
		else:
			inputs = action.split()
			if len(inputs) == 2:
				try:
					gain = int(inputs[0])  #gain
					exposure = int(inputs[1])  # Exposure Time en µs
					picam2.set_controls({"AnalogueGain": gain, "ExposureTime": exposure})
					time.sleep(2)
				except ValueError:
					print(" Erreur : Entrée invalide, veuillez entrer deux nombres (ex: '50000 2000') ou juste 'Entrée' pour utiliser les derniers réglages.")
					continue
			nom_fichier = os.path.join(dossier_destination, f"pi0_{id}_gain_{gain}_exposure_{exposure}.jpg")
			picam2.capture_file(nom_fichier)
			print(f"Photo {id} prise et enregistrée sous {nom_fichier}")
			id += 1


if __name__ == "__main__":
    broadcast_Picture()