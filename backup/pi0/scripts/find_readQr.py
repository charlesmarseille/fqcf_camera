import cv2
import sys
import json
import piexif
import piexif.helper
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np
import zxingcpp

def supprimer_usercomment(image_path):
    """Efface uniquement la métadonnée UserComment sans toucher aux autres EXIF."""
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")

        if not exif_data:
            return  # Aucun EXIF, donc rien à supprimer

        exif_dict = piexif.load(exif_data)

        # Supprimer seulement UserComment
        if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
            del exif_dict["Exif"][piexif.ExifIFD.UserComment]
            print(f"UserComment supprimé pour {image_path}")

            # Sauvegarde sans UserComment
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes)

    except Exception as e:
        print(f"Erreur lors de la suppression de UserComment dans {image_path} : {e}")

def detecter_qr_et_ajouter_metadata(image_path):
    """Détecte un QR Code dans une photo et enregistre son contenu dans les métadonnées EXIF"""
    print(f" Chargement de l'image : {image_path}")

    supprimer_usercomment(image_path)

    # Charger l'image avec OpenCV
    image = Image.open(image_path)

    if image is None:
        print(f" Erreur: Impossible de charger l'image {image_path}")
        return

    # Détecter les codes QR dans l'image
    results = zxingcpp.read_barcodes(image)
    if len(results) != 0:
        print(results)
        for result in results:
            text = result.text.strip()
            print(f" QR Code détecté :\n{text}")
    else:
        return None

    # Extraire les informations du QR Code
    infos_qr = {}
    for ligne in text.split("\n"):
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