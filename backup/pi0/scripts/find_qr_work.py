import cv2
import sys
import json
import piexif
import piexif.helper
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np

def detecter_qr_et_ajouter_metadata(image_path):
    """Détecte un QR Code dans une photo et enregistre son contenu dans les métadonnées EXIF"""
    print(f" Chargement de l'image : {image_path}")

    # Charger l'image avec OpenCV
    image = cv2.imread(image_path)

    if image is None:
        print(f" Erreur: Impossible de charger l'image {image_path}")
        return

    # Détecter les codes QR dans l'image
    qr_codes = decode(image)

    if len(qr_codes)==0:
        print(" Aucun QR Code détecté.")
        return
    
    # Prendre le premier QR détecté
    if len(qr_codes) >1:
        for qr_code in qr_codes:
            print(qr_code)
        qr_code = qr_codes[len(qr_codes)-1]
        qr_data = qr_code.data.decode("utf-8").strip()
    else:
        qr_code = qr_codes[0]
        qr_data = qr_code.data.decode("utf-8").strip()
    
    print(f" QR Code détecté :\n{qr_data}")

    # Extraire les informations du QR Code
    infos_qr = {}
    for ligne in qr_data.split("\n"):
        if ": " in ligne:
            cle, valeur = ligne.split(": ", 1)
            infos_qr[cle.strip()] = valeur.strip()

    # Charger l'image avec PIL pour modifier les métadonnées
    img = Image.open(image_path)

    # Vérifier si l'image supporte EXIF
    if img.format not in ["JPEG", "TIFF"]:
        print(" L'image ne supporte pas EXIF. Utilisez JPEG ou TIFF.")
        return
    
    # Charger ou créer les métadonnées EXIF
    exif_dict = piexif.load(img.info.get("exif", b""))

    # Stocker toutes les données sous forme de JSON dans UserComment
    json_metadata = json.dumps(infos_qr)
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json_metadata, encoding="unicode")

    # Sauvegarder avec EXIF
    exif_bytes = piexif.dump(exif_dict)
    img.save(image_path, exif=exif_bytes)

    print(f" Métadonnées ajoutées à {image_path}")

# Vérifier l'utilisation du script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilisation: python script_qr.py <chemin_vers_image>")
    else:
        detecter_qr_et_ajouter_metadata(sys.argv[1])