#!/bin/bash

# Variables
REMOTE_USER="pi0"
REMOTE_HOST="192.168.0.100"
SSH_KEY="$HOME/.ssh/id_rsa"

# Génération de la clé SSH si elle n'existe pas
if [ ! -f "$SSH_KEY" ]; then
    echo "Génération d'une nouvelle clé SSH..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY" -N ""
else
    echo "La clé SSH existe déjà : $SSH_KEY"
fi

# Copie de la clé publique vers le dossier ~/.ssh/authorized_keys sur le serveur distant
echo "Ajout de la clé publique au fichier authorized_keys sur le serveur distant..."
ssh-copy-id -i "$SSH_KEY.pub" "$REMOTE_USER@$REMOTE_HOST"

# Test de la connexion SSH
echo "Test de la connexion SSH..."
if ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" exit; then
    echo "Connexion SSH sans mot de passe réussie !"
else
    echo "Échec de la connexion SSH. Veuillez vérifier les configurations."
fi
