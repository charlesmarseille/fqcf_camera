import time
import socket
import os
from datetime import datetime



# Configuration
PORT = 12344  # Port d'envoi des requête
BROADCAST_IP = "255.255.255.255"  # Adresse de broadcast pour envoyer à tous les RPi
HEADER = "Photo"  # Entête pour identifier les paquets
config_send_sucessful = True


def broadcast_Picture():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

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