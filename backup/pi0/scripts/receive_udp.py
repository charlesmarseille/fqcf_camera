import socket
import os
import sys
import numpy as np

PORT = 12344
BUFFER_SIZE = 99999
HEADER = "Envoi_Photo"
IP= "0.0.0.0"

dossier_destination = "/mnt/ssd/backup/1/"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IP, PORT))
sock.listen(1)

while True:
    conn, addr = sock.accept()
    print(f"Connexion acceptée de {addr}")

    # Lire la taille des métadonnées
    metadata_size = int.from_bytes(conn.recv(4), "big")
    metadata = conn.recv(metadata_size).decode()

    # Extraire nom, shape et dtype
    nom_fichier, shape, dtype = metadata.split(":")
    try:
        # Vérifier que `shape` contient bien des chiffres avant la conversion
        shape = tuple(map(int, filter(None, shape.strip("()").split(","))))
    except ValueError:
        print(f"Erreur : format de `shape` invalide -> {shape}")
        continue

    # Lire la taille du buffer
    buffer_size = int.from_bytes(conn.recv(4), "big")

    # Lire le buffer
    buffer = b""
    while len(buffer) < buffer_size:
        buffer += conn.recv(buffer_size - len(buffer))

    # Reconstruction
    array = np.frombuffer(buffer, dtype=dtype).reshape(shape)

    # Sauvegarde
    with open(nom_fichier, "wb") as img_file:
        img_file.write(array.tobytes())

    print(f"Image reçue et enregistrée sous {nom_fichier}")

    conn.close()