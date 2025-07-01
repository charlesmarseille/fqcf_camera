import cv2
import sys
import numpy as np
import matplotlib.pyplot as plt
import os

def afficher_histogramme(image_path, output_folder="output_histograms"):
    """Affiche et enregistre un histogramme de la distribution des niveaux de gris d'une image."""
    # Charger l'image en niveaux de gris
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        return
    
    # Calculer l'histogramme
    histogram = cv2.calcHist([img], [0], None, [256], [0, 256])
    
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Nom du fichier de sortie
    base_name = os.path.basename(image_path)
    output_path = os.path.join(output_folder, f"{os.path.splitext(base_name)[0]}_histogramme.png")
    
    # Afficher et enregistrer l'histogramme
    plt.figure(figsize=(10, 5))
    plt.plot(histogram, color='black')
    plt.title("Distribution des niveaux de gris")
    plt.xlabel("Valeur des pixels (0-255)")
    plt.ylabel("Nombre de pixels")
    plt.xlim([0, 255])
    plt.grid()
    plt.savefig(output_path)
    plt.close()
    
    print(f"Histogramme enregistré : {output_path}")

# Vérifier l'utilisation du script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilisation: python histogramme.py <chemin_vers_image>")
    else:
        afficher_histogramme(sys.argv[1])