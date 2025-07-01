import socket
import os
import sys
from datetime import datetime
from systemd import daemon
import netifaces

# Configuration
PORT = 12345  # Port d'écoute
BUFFER_SIZE = 1024  # Taille du buffer de réception
INTERFACE = "eth0"  # Interface réseau spécifique

def get_eth0_ip():
    """Récupère l'adresse IP de l'interface eth0."""
    try:
        return netifaces.ifaddresses(INTERFACE)[netifaces.AF_INET][0]['addr']
    except KeyError:
        print(f"Impossible de récupérer l'adresse IP de {INTERFACE}")
        sys.exit(1)

def set_system_time(timestamp_str):
    """Met à jour l'horloge système avec le timestamp reçu."""
    try:
        os.system(f"sudo date -s '{timestamp_str}'")
        print(f"Heure mise à jour: {timestamp_str}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'heure: {e}")

def receive_timestamp():
    """Écoute le broadcast UDP pour recevoir l'horodatage et mettre à jour l'horloge locale."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))  # Écoute sur toutes les interfaces pour voir tous les paquets
    print(f"En attente de l'horodatage au port {PORT}...")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode().strip()
            print(f"Paquet reçu de {addr}: {message}")
            
            if message.startswith("TIMESTAMP_SYNC:"):
                timestamp_str = message.split("TIMESTAMP_SYNC:")[1].strip()
                set_system_time(timestamp_str)
            else:
                print("Paquet ignoré, format invalide.")
        except Exception as e:
            print(f"Erreur lors de la réception du paquet: {e}")

if __name__ == "__main__":
    receive_timestamp()
