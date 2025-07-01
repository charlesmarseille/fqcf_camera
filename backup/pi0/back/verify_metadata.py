import os
import json
from PIL import Image
import piexif
import piexif.helper

# Dossier contenant les images (MODIFIER CE CHEMIN)
DOSSIER_IMAGES = "/home/pi0/test_qr/mat/"  #  À modifier avec le bon chemin

def lire_metadonnees(image_path):
    """Lit et affiche les métadonnées JSON stockées dans UserComment si elles existent."""
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")

        if not exif_data:
            return None  #  Pas d'EXIF du tout

        exif_dict = piexif.load(exif_data)
        user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")

        if user_comment:
            try:
                json_data = piexif.helper.UserComment.load(user_comment)
                metadata = json.loads(json_data)  #  Vérifie si le JSON est valide
                return metadata if metadata else None  #  Retourne les métadonnées si elles existent
            except json.JSONDecodeError:
                return None  #  JSON invalide
        else:
            return None  #  UserComment vide

    except Exception as e:
        print(f" Erreur lors de la lecture des métadonnées de {image_path} : {e}")
        return None

def detecter_images_sans_metadata(dossier):
    """Liste toutes les images et affiche leurs métadonnées si disponibles."""
    total_images = 0
    images_sans_metadata = []

    # Vérifier si le dossier existe
    if not os.path.isdir(dossier):
        print(f" Erreur: Le dossier spécifié '{dossier}' n'existe pas.")
        return

    print(f" Vérification des métadonnées dans le dossier : {dossier}\n")

    # Parcourir toutes les images du dossier
    for fichier in sorted(os.listdir(dossier)):  # Trier pour un affichage propre
        chemin_fichier = os.path.join(dossier, fichier)

        # Vérifier si c'est une image (formats supportés)
        if fichier.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
            total_images += 1

            # Lire les métadonnées
            metadata = lire_metadonnees(chemin_fichier)

            if metadata:
                print(f" Métadonnées trouvées pour {fichier} :")
                print(json.dumps(metadata, indent=2))  # Affichage formaté du JSON
            else:
                images_sans_metadata.append(fichier)

    # Résumé final
    print("\n **Résumé de l'analyse**")
    print(f" Nombre total d'images analysées : {total_images}")
    print(f" Nombre d'images SANS métadonnées : {len(images_sans_metadata)}")
    print(f" Nombre d'images AVEC métadonnées : {total_images - len(images_sans_metadata)}")

    # Afficher la liste des images sans métadonnées
    if images_sans_metadata:
        print("\n **Liste des images sans métadonnées EXIF (UserComment absent ou vide) :**")
        for img in images_sans_metadata:
            print(f"   - {img}")
    else:
        print("\n Toutes les images ont des métadonnées EXIF UserComment.")

# Lancer la vérification
if __name__ == "__main__":
    detecter_images_sans_metadata(DOSSIER_IMAGES)
