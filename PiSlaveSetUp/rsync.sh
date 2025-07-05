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
    # Synchroniser les fichiers sans supprimer ceux du source
    rsync -avz "$SOURCE" "$DEST"

    # Vérifier l'utilisation du disque sur le répertoire source
    USAGE=$(df "$SOURCE" | awk 'NR==2 {print $5}' | tr -d '%')

    # Supprimer les fichiers les plus anciens seulement si l'utilisation dépasse 50%
    if [ "$USAGE" -ge 50 ]; then
        # Trouver les fichiers les plus anciens et les supprimer jusqu'à ce que l'utilisation soit < 50%
        while [ "$USAGE" -ge 50 ]; do
            OLDEST_FILE=$(find "$SOURCE" -type f -printf '%T+ %p\n' | sort | head -n 1 | awk '{print $2}')
            if [ -n "$OLDEST_FILE" ]; then
                rm -f "$OLDEST_FILE"
            else
                break
            fi
            USAGE=$(df "$SOURCE" | awk 'NR==2 {print $5}' | tr -d '%')
        done
        # Nettoyer les répertoires vides
        find "$SOURCE" -type d -empty -delete
    fi
    sleep 5
done