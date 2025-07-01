import cv2
import sys
import json
import os
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

def calculer_median(image_path):
    """Calcule la médiane des valeurs de pixels en niveaux de gris."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        return None
    return int(np.median(img))

def binariser_image(image_path, threshold=160, output_folder="output_images"):
    """Convertit une image en noir et blanc en appliquant un seuil et l'enregistre dans un dossier spécifique sans métadonnées."""
    # Charger l'image en niveaux de gris
    threshold = calculer_median(image_path)
    if threshold is None:
        return None

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        return None
    
    # Appliquer un seuillage binaire
    _, binary_img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Construire le chemin de sortie
    output_path = os.path.join(output_folder, os.path.basename(image_path))
    
    # Sauvegarder l'image transformée sans métadonnées
    cv2.imwrite(output_path, binary_img)
    print(f"Image binaire enregistrée : {output_path}")
    
    return output_path

def detecter_qr_et_ajouter_metadata(image_path):
    """Détecte un QR Code dans une photo et enregistre son contenu dans les métadonnées EXIF de l'image originale."""
    print(f"Chargement de l'image : {image_path}")

    supprimer_usercomment(image_path)
    
    # Appliquer le masque (seuillage) et enregistrer l'image
    image_binarisee_path = binariser_image(image_path, threshold=160)
    if image_binarisee_path is None:
        return
    
    # Charger l'image binaire avec PIL pour détecter le QR Code
    image_binarisee = Image.open(image_binarisee_path)
    
    # Détecter les codes QR dans l'image
    results = zxingcpp.read_barcodes(image_binarisee)
    if not results:
        print("Aucun QR Code détecté.")
        return
    
    # Extraire les informations du QR Code
    infos_qr = {}
    for result in results:
        text = result.text.strip()
        print(f"QR Code détecté :\n{text}")
        for ligne in text.split("\n"):
            if ": " in ligne:
                cle, valeur = ligne.split(": ", 1)
                infos_qr[cle.strip()] = valeur.strip()
    
    # Charger l'image originale pour modifier ses métadonnées
    image_originale = Image.open(image_path)
    
    # Vérifier si l'image supporte EXIF
    if image_originale.format not in ["JPEG", "TIFF"]:
        print("L'image ne supporte pas EXIF. Utilisez JPEG ou TIFF.")
        return
    
    # Charger ou créer les métadonnées EXIF
    exif_dict = piexif.load(image_originale.info.get("exif", b""))
    
    # Stocker les données sous forme de JSON dans UserComment
    json_metadata = json.dumps(infos_qr)
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json_metadata, encoding="unicode")
    
    # Sauvegarder avec EXIF dans l'image originale
    exif_bytes = piexif.dump(exif_dict)
    image_originale.save(image_path, exif=exif_bytes)
    
    print(f"Métadonnées ajoutées à {image_path}")

# Vérifier l'utilisation du script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilisation: python script_qr.py <chemin_vers_image>")
    else:
        detecter_qr_et_ajouter_metadata(sys.argv[1])