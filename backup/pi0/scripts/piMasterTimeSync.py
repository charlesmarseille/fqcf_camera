import time
import socket
import ntplib
import os
from datetime import datetime
from systemd import daemon

# Configuration
PORT = 12345  # Port d'envoi des timestamps
BROADCAST_IP = "255.255.255.255"  # Adresse de broadcast pour envoyer à tous les RPi
NTP_SERVER = "pool.ntp.org"  # Serveur NTP
HEADER = "TIMESTAMP_SYNC"  # Entête pour identifier les paquets


def get_ntp_time():
    """Récupère l'heure depuis un serveur NTP et met à jour l'horloge locale."""
    try:
        client = ntplib.NTPClient()
        response = client.request(NTP_SERVER, version=3)
        timestamp = datetime.utcfromtimestamp(response.tx_time).strftime('%Y-%m-%d %H:%M:%S')
        os.system(f"sudo date -s '{timestamp}'")  # Mise à jour de l'horloge système
        return timestamp
    except Exception as e:
        print(f"Erreur lors de la récupération de l'heure NTP : {e}")
        return None


def broadcast_timestamp():
    """Envoie l'horodatage à tous les Raspberry Pi du réseau avec une entête."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        timestamp = get_ntp_time()
        if timestamp:
            message = f"{HEADER}:{timestamp}".encode()
            sock.sendto(message, (BROADCAST_IP, PORT))
            print(f"Horodatage envoyé: {message}")
        else:
            print("Impossible de récupérer l'heure.")
        time.sleep(10)  # Envoi toutes les 10 secondes


if __name__ == "__main__":
    broadcast_timestamp()
