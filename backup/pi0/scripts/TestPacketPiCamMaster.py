import time
import socket
import ntplib
import os
import json
from datetime import datetime
from picamera2 import Picamera2



# Configuration
PORT = 12344  # Port d'envoi des requête
BROADCAST_IP = "255.255.255.255"  # Adresse de broadcast pour envoyer à tous les RPi
HEADER = "Photo"  # Entête pour identifier les paquets
config_send_sucessful = True

def send_config(config, ip_list, port=5000):
    """ Envoie toute la configuration sous forme de string aux IPs spécifiées """
    tosend = json.dumps(config).encode('utf-8')
    for ip in ip_list:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
                try:
                    tcp_sock.connect((ip, port))  # Connexion
                    tcp_sock.sendall(tosend)  # Envoi
                    print(f" Configuration envoyée avec succès à {ip}")

                except ConnectionResetError:
                    config_send_sucessful = False
                    print(f"Erreur lors de l'initialisation de la configuration sur le pi {ip}")
                except ConnectionRefusedError:
                    print(f" Erreur : Connexion refusée à {ip}. Vérifie que le serveur est bien lancé.")
                    config_send_sucessful = False
                except Exception as e:
                    print(f" Erreur lors de l'envoi à {ip}: {e}")
                    config_send_sucessful = False

def broadcast_Picture():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    picam2 = Picamera2()
    
    # Configuration initiale avec auto-réglages
    picam2.configure(picam2.create_still_configuration(main={"format": "RGB888", "size": (4608, 2592)},
                                                        controls={"AfMode": 0, "LensPosition": 1.2, "NoiseReductionMode": 0})) #autofocus a off et focus environ 90cm
    picam2.start() # démarage des paramètre auto-expositon auto-balance
    time.sleep(3)  # Laisser le temps à l'auto-exposition et l'auto-balance de s'ajuster
    
    # Récupérer les paramètres après auto-ajustement
    metadata = picam2.capture_metadata()
    picam2.stop()
    # Désactiver les réglages automatiques et appliquer les valeurs enregistrées
    config_verrouillee = {
        "AwbEnable": False,
        "AeEnable": False,
        # n'est pas automatiquement ajusté 
        #"Brightness": metadata.get("Brightness", 0.0), 
        #"Contrast": metadata.get("Contrast", 0.0),
        #"Saturation": metadata.get("Saturation", 0.0),
        #"Sharpness": metadata.get("Sharpness", 0.0),
        #automatiquement ajusté
        "ExposureTime": metadata.get("ExposureTime", 1000),
        "AnalogueGain": metadata.get("AnalogueGain", 1.0),
        "ColourGains": metadata.get("ColourGains", (1.0, 1.0)),
    }
    #print(config_verrouillee)
    
    config = picam2.create_still_configuration(main={"format": "RGB888", "size": (4608, 2592)},
                                                        controls={**config_verrouillee, "AfMode": 0, "LensPosition": 1.2})#"NoiseReductionMode": 0
    picam2.configure(config)

    print(config)

    #serialized_config = serialize_config(config)
    picam2.start()
    ip_list = ["192.168.0.101", "192.168.0.103"]  # "192.168.0.103",
    config_to_send = {k: v for k, v in config.items() if k != 'transform' and k != 'colour_space' }
    if "controls" in config_to_send:
        config_to_send["controls"] = {k: v for k, v in config_to_send["controls"].items() if k != "NoiseReductionMode"}
    send_config(config_to_send, ip_list, 5000)

    # Dossier de destination
    dossier_destination = "/mnt/ssd/backup/0/"
    os.makedirs(dossier_destination, exist_ok=True)

    id = 0
    while config_send_sucessful: # si la config a bien été envoyé et décodé, prend des photos, sinon le script arrête son exécution
        message = f"{HEADER}:{id}".encode() #id
        sock.sendto(message, (BROADCAST_IP, PORT))
        nom_fichier = os.path.join(dossier_destination, "pi0_"+ str(id) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3] + ".jpg") #date format YYYYMMDD_HHMMSSmmm
        os.mknod(nom_fichier)
        print(id)
        id +=1
        time.sleep(1)
        


if __name__ == "__main__":
    broadcast_Picture()