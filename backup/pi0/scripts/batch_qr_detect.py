import os
import subprocess
import json
from PIL import Image
import piexif
import piexif.helper

# Dossier contenant les images (MODIFIER CE CHEMIN)
DOSSIER_IMAGES = "/home/pi0/test_qr/mat/"  # À modifier avec le bon chemin
SCRIPT_QR = "find_readQrMask.py"  # Nom du premier script

def lire_usercomment(image_path):
    """Vérifie si un QR Code est bien présent dans UserComment et retourne True si trouvé."""
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")

        if not exif_data:
            return False

        exif_dict = piexif.load(exif_data)
        user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")

        if user_comment:
            try:
                json_data = piexif.helper.UserComment.load(user_comment)
                metadata = json.loads(json_data)  # Vérifie si le JSON est bien valide
                return bool(metadata)  # Retourne True si des données sont présentes
            except json.JSONDecodeError:
                return False  # Si le JSON est invalide, considère qu'il n'y a pas de données

    except Exception as e:
        print(f"Erreur lors de la lecture des métadonnées : {e}")
    
    return False

def traiter_images(dossier):
    """Lance script_qr.py sur chaque image du dossier et vérifie si les métadonnées ont été ajoutées."""
    total_images = 0
    images_avec_qr = 0

    # Vérifier si le dossier existe
    if not os.path.isdir(dossier):
        print(f"Erreur: Le dossier spécifié '{dossier}' n'existe pas.")
        return

    # Parcourir tous les fichiers du dossier
    for fichier in sorted(os.listdir(dossier)):
        chemin_fichier = os.path.join(dossier, fichier)

        # Vérifier si c'est une image (formats courants)
        if fichier.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
            total_images += 1
            print(f"traitement de : {fichier}")

            # Exécuter le premier script (sans afficher de sortie)
            subprocess.run(["python", SCRIPT_QR, chemin_fichier], text=True)

            # Vérifier si UserComment contient des données JSON valides
            if lire_usercomment(chemin_fichier):
                images_avec_qr += 1

    # Résumé final
    print(f"\n **Résumé du traitement pour {dossier} **")
    print(f" Nombre total d'images traitées : {total_images}")
    print(f" Nombre d'images avec un QR Code enregistré : {images_avec_qr}")
    print(f" Pourcentage de succès : {100 * images_avec_qr / total_images:.2f}%" if total_images > 0 else "Aucune image traitée.")

# Lancer le traitement
if __name__ == "__main__":
    traiter_images(DOSSIER_IMAGES)
    #for sous_dossier in os.listdir(DOSSIER_IMAGES):
    #    chemin_sous_dossier = os.path.join(DOSSIER_IMAGES, sous_dossier)

#        if os.path.isdir(chemin_sous_dossier):
#            print(f"\n Traitement du sous-dossier : {sous_dossier}")
#            traiter_images(chemin_sous_dossier)

