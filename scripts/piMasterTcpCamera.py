import time
import socket
import os
from datetime import datetime
from picamera2 import Picamera2
import glob
import threading

# Configuration
PORT = 12344  # Port d'envoi des requêtes

pi_numbers = [1,2,3,4,5,6] # Liste des numéros de Raspberry Pi (1 à 6)
pi_ips = [f"192.168.0.10{pi_number}" for pi_number in pi_numbers]
HEADER = "Photo"  # Entête pour identifier les paquets

def send_tcp_message(server_ip, port, message):
    """Envoie un message TCP à une adresse IP spécifique"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print(f"Connecting to {server_ip}:{port} with message: {message}")
            sock.settimeout(2)  # Timeout de 2 secondes pour éviter le blocage
            sock.connect((server_ip, port))
            sock.sendall(message.encode())
            response = sock.recv(1024).decode()
            print(f"Response from {server_ip}: {response}")
    except Exception as e:
        print(f"Error in comms to {server_ip}: {e}")

def capture_picture():
    """Capture une photo après l'envoi des requêtes TCP"""
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration(main={"format": "RGB888", "size": (4608,2592)}))
    picam2.start()

    dossier_destination = "/mnt/ssd/backup/0/"
    os.makedirs(dossier_destination, exist_ok=True)
    # Chercher le dernier id utilisé dans le dossier de destination
    pattern = os.path.join(dossier_destination, "pi0_*.jpg")
    files = glob.glob(pattern)
    if files:
        # Extraire les ids et trouver le max
        ids = []
        for f in files:
            basename = os.path.basename(f)
            parts = basename.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                ids.append(int(parts[1]))
        last_id = max(ids) + 1 if ids else 0
    else:
        # Aucun fichier trouvé, commencer à 0
        print("No previous images found on master pi0, starting with id 0.")
        last_id = 0

    id = last_id
    while True:
        message = f"{HEADER}:{id}"

        # Capture de l'image après la transmission des messages
        nom_fichier = os.path.join(
            dossier_destination,
            f"pi0_{id:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]}.jpg"
        )

        # Envoi de la requête TCP aux six serveurs en parallèle

        def capture_image():
            picam2.capture_file(nom_fichier)

        threads = []
        for ip in pi_ips:
            start = datetime.now()
            print('time: ', start.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            t = threading.Thread(target=send_tcp_message, args=(ip, PORT, message))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
            
        capture_delay = 0.3  # delay in seconds before capturing the image
        print('time difference after sending messages: ', (datetime.now() - start).total_seconds(), 'seconds')
        capture_thread = threading.Timer(capture_delay, capture_image)
        capture_thread.start()
        capture_thread.join()
        time_after_capture = datetime.now()
        print('time difference after capture: ', (time_after_capture - start).total_seconds(), 'seconds')

        if os.path.getsize(nom_fichier) > 1000:
            print(f"Image captured and saved as {nom_fichier}")
            id += 1
            time.sleep(0.5)
        else:
            print(f"Failed to capture image for id {id}")

if __name__ == "__main__":
    capture_picture()
