#!/bin/bash

# Script de déploiement pour FlashNotify
# Ce script déploie l'application dans différents environnements

set -e  # Arrête le script en cas d'erreur

# Configuration des variables
APP_NAME="flashnotify"
IMAGE_NAME="flashnotify-app"
CONTAINER_NAME="flashnotify-container"
DEFAULT_ENV="dev"
DEFAULT_PORT="8000"

# Fonction d'aide
show_help() {
    echo "Usage: $0 [ENVIRONMENT]"
    echo ""
    echo "Déploie l'application FlashNotify dans l'environnement spécifié."
    echo ""
    echo "Environnements disponibles:"
    echo "  dev     - Développement (par défaut)"
    echo "  staging - Pré-production"
    echo " prod    - Production"
    echo ""
    echo "Options:"
    echo "  -h, --help    Affiche cette aide"
    echo "  -r, --rebuild Force la reconstruction de l'image Docker"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Déploie en environnement dev"
    echo "  $0 prod              # Déploie en production"
    echo "  $0 staging -r        # Déploie en staging avec reconstruction"
}

# Variables par défaut
ENVIRONMENT=$DEFAULT_ENV
REBUILD=false

# Traitement des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -*)
            echo "Option inconnue: $1"
            echo "Utilisez $0 --help pour plus d'informations"
            exit 1
            ;;
        *)
            ENVIRONMENT="$1"
            shift
            ;;
    esac
done

# Validation de l'environnement
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "Environnement invalide: $ENVIRONMENT"
    echo "Les environnements valides sont: dev, staging, prod"
    exit 1
fi

echo "=== Déploiement de $APP_NAME dans l'environnement $ENVIRONMENT ==="

# Chargement des variables d'environnement spécifiques
ENV_FILE=".env.${ENVIRONMENT}"
if [ -f "$ENV_FILE" ]; then
    echo "Chargement des variables d'environnement depuis $ENV_FILE"
    export $(cat "$ENV_FILE" | xargs)
else
    echo "Fichier $ENV_FILE non trouvé, utilisation des valeurs par défaut"
fi

# Construction de l'image Docker
if [ "$REBUILD" = true ] || [ ! "$(docker images -q $IMAGE_NAME 2> /dev/null)" ]; then
    echo "Construction de l'image Docker..."
    docker build -t $IMAGE_NAME .
    echo "Image Docker construite avec succès"
else
    echo "L'image Docker existe déjà. Utilisation de l'image existante."
    if [ "$REBUILD" = true ]; then
        echo "Reconstruction de l'image Docker demandée..."
        docker build -t $IMAGE_NAME --no-cache .
        echo "Image Docker reconstruite avec succès"
    fi
fi

# Arrêt et suppression du conteneur existant
if [ "$(docker ps -aq -f name=$CONTAINER_NAME 2> /dev/null)" ]; then
    echo "Arrêt du conteneur existant..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    echo "Suppression du conteneur existant..."
    docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
fi

# Détermination du port en fonction de l'environnement
case $ENVIRONMENT in
    "dev")
        PORT=8000
        ;;
    "staging")
        PORT=8080
        ;;
    "prod")
        PORT=80
        ;;
esac

# Lancement du conteneur
echo "Lancement du conteneur $CONTAINER_NAME sur le port $PORT..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:8000 \
    -e ENVIRONMENT=$ENVIRONMENT \
    -e FASTAPI_PORT=8000 \
    -e DATABASE_URL=${DATABASE_URL:-sqlite:///./flashnotify.db} \
    -e REDIS_URL=${REDIS_URL:-redis://localhost:6379/0} \
    -e SESSION_SECRET=${SESSION_SECRET:-dev-secret-key-change-in-production} \
    $IMAGE_NAME

echo "Conteneur $CONTAINER_NAME lancé avec succès sur le port $PORT"

# Vérification du statut du conteneur
sleep 5
if [ "$(docker ps -q -f name=$CONTAINER_NAME 2> /dev/null)" ]; then
    echo "=== Déploiement terminé avec succès ==="
    echo "Application disponible sur http://localhost:$PORT"
    docker ps -f name=$CONTAINER_NAME
else
    echo "Erreur: Le conteneur ne s'est pas lancé correctement"
    docker logs $CONTAINER_NAME
    exit 1
fi