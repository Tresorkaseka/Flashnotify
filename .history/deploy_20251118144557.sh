
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
