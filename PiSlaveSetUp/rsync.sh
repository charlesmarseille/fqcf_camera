#!/bin/bash

# Répertoire source sur le Pi Zero
SOURCE="/home/$(hostname)/photo/"

# Extraire le dernier caractère du hostname
HOSTNAME_LAST_CHAR=$(hostname | tail -c 2)

# Destination sur le Pi 4 avec le dernier caractère du hostname
DEST="pi0@192.168.0.100:/mnt/ssd/backup/$HOSTNAME_LAST_CHAR/"

echo "Démarrage du processus de synchronisation continue vers $DEST..."

# Boucle infinie pour surveiller et synchroniser les fichiers
while true; do
    # Synchroniser les fichiers et supprimer ceux du source après transfert
    rsync -avz --remove-source-files "$SOURCE" "$DEST"

    # Nettoyer les répertoires vides
    find "$SOURCE" -type d -empty -delete

    sleep 5
done
