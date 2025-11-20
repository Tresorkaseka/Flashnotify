# Documentation Technique FlashNotify

## Vue d'Ensemble

Cette documentation technique complète présente l'architecture, l'API, les guides de développement et la justification des choix techniques du système de notification académique FlashNotify.

## Structure de la Documentation

### 📁 [Guide d'Architecture](architecture/README.md)
- Vue d'ensemble de l'architecture système
- Diagrammes de classes UML détaillés
- Patterns de conception utilisés (Métaclasses, Décorateurs, Mixins)
- Flux de données et composants de base de données
- Diagrammes de séquence pour les processus clés

**Points clés couverts :**
- Architecture hybride Flask/FastAPI
- Système de notification avec mixins et héritage multiple
- Métaclasses pour auto-configuration
- Circuit breaker et gestion des performances
- Modèles SQLAlchemy et structure des données

### 📁 [Documentation API](api/openapi.yaml)
- Spécification OpenAPI 3.0 complète
- Documentation de tous les endpoints avec exemples
- Guide d'authentification API (JWT, API Keys)
- Formats de requête/réponse détaillés
- Codes d'erreur et réponses d'exception

**Endpoints documentés :**
- `/api/v2/users/` - Gestion des utilisateurs
- `/api/v2/notifications/` - Envoi et gestion des notifications
- `/api/v2/stats/` - Statistiques système
- `/api/v2/performance/` - Métriques de performance
- `/api/v2/health/` - Vérification de santé

### 📁 [Guide de Développement](development/extending-guide.md)
- Configuration de l'environnement de développement
- Architecture et patterns détaillés
- Comment étendre le système de notification
- Guide pour ajouter de nouveaux canaux (Slack, Discord, etc.)
- Création de nouveaux types de notificateurs
- Bonnes pratiques de développement
- Guide de debugging et de test
- Stratégies de déploiement

**Fonctionnalités couvertes :**
- Ajout de nouveaux types d'urgence
- Création de mixins personnalisés
- Implémentation de notificateurs spécialisés
- Tests unitaires et d'intégration
- Monitoring et métriques

### 📁 [Justification des Choix Techniques](technical-decisions/choices-justification.md)
- Justification approfondie des choix d'architecture
- Analyse des alternatives évaluées
- Patterns de conception expliqués
- Sécurité et authentification multi-couches
- Performance et scalabilité
- Décisions controversées et leurs justifications
- Évolutions futures et roadmap technique

**Décisions techniques justifiées :**
- Architecture hybride Flask/FastAPI
- Métaclasses vs alternatives
- Mixins vs composition
- Queue custom vs Redis/Celery
- SQLite vs PostgreSQL
- Circuit breaker pattern
- Registry pattern pour auto-découverte

## Technologies Principales

### Backend
- **Python 3.8+** : Langage principal
- **Flask** : Application web et interface utilisateur
- **FastAPI** : API REST moderne avec documentation auto-générée
- **SQLAlchemy** : ORM pour la base de données

### Base de Données
- **SQLite** : Développement (zero configuration)
- **PostgreSQL** : Production (scalabilité, fonctionnalités avancées)

### Patterns Avancés
- **Métaclasses** : Auto-configuration et génération de code
- **Décorateurs** : Fonctionnalités transverses (performance, circuit breaker)
- **Mixins** : Héritage multiple contrôlé pour la composition
- **Descripteurs** : Validation automatique des données

### Sécurité
- **JWT** : Authentification pour API modernes
- **API Keys** : Accès programmatique
- **Sessions Flask** : Interface web traditionnelle
- **Validation** : Descripteurs et métaclasses

### Performance
- **Files d'attente** : ThreadPoolExecutor + AsyncIO
- **Circuit Breaker** : Protection contre les cascading failures
- **Métriques** : Surveillance automatique des performances

## Démarrage Rapide

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd FlashNotify

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
python reset_db.py

# Lancer l'application
python app.py
```

### API Documentation
Une fois l'application lancée :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Spécification OpenAPI** : `/api/openapi.yaml`

### Interface Web
- **Application** : http://localhost:5000
- **Admin Dashboard** : http://localhost:5000/admin
- **API Stats** : http://localhost:5000/dashboard

## Architecture du Projet

```
FlashNotify/
├── core/                     # Logique métier pure
│   ├── notification_system.py    # Système principal
│   ├── metaclasses.py           # Métaclasses
│   ├── decorators.py            # Décorateurs
│   ├── descriptors.py           # Descripteurs
│   ├── auth.py                  # Authentification
│   └── queue.py                 # Files d'attente
├── api/                      # API FastAPI
│   └── main.py
├── models.py                # Modèles SQLAlchemy
├── app.py                   # Application Flask
├── templates/               # Interface web
├── static/                  # Assets web
├── tests/                   # Tests unitaires
└── documentation/           # Documentation technique
    ├── architecture/
    ├── api/
    ├── development/
    └── technical-decisions/
```

## Patterns Clés

### 1. Métaclasses pour Auto-Configuration
```python
@auto_configuration_validation
class AcademicNotifier(SMSMixin, EmailMixin, PushNotificationMixin, ...):
    required_fields = ['title', 'body']
    # Configuration automatique appliquée
```

### 2. Mixins pour Composition
```python
class AcademicNotifier(EmailMixin, SMSMixin, PushNotificationMixin):
    pass
# Héritage multiple flexible
```

### 3. Décorateurs Transverses
```python
@add_performance_tracking
@add_circuit_breaker(max_failures=5)
def send_notification(self, data):
    # Surveillance automatique appliquée
```

### 4. Registry Pattern
```python
@register_in_global_registry
class AcademicNotifier(...):
    pass
# Auto-enregistrement au chargement
```

## Cas d'Usage

### Envoi de Notification Simple
```python
notifier = AcademicNotifier()
result = notifier.notify(
    user={'email': 'user@example.com', 'phone': '+33123456789'},
    title="Fermeture Bibliothèque",
    body="La bibliothèque ferme à 18h aujourd'hui",
    emergency_type=EmergencyType.ACADEMIC
)
```

### Ajout d'un Nouveau Canal
```python
class SlackMixin:
    channel_type = 'slack'
    
    def send_slack(self, message, channel):
        # Implémentation Slack
        pass

class AcademicNotifier(SMSMixin, EmailMixin, SlackMixin, ...):
    pass
```

### Extension avec Nouveau Notificateur
```python
@add_performance_tracking
class MedicalNotifier(SMSMixin, EmailMixin, PushNotificationMixin, ...):
    def notify_medical_emergency(self, patient_data, emergency_type, level):
        # Logique médicale spécialisée
        pass
```

## Métriques et Monitoring

### Performance
- Temps d'exécution par canal (Email, SMS, Push)
- Taux de succès/échec par méthode
- Métriques de circuit breaker
- Surveillance automatique intégrée

### Santé Système
- Endpoint `/api/v2/health/` pour vérifications
- Circuit breaker status
- Queue status et worker health
- Database connectivity

## Évolutions Futures

### Court Terme (3-6 mois)
- Cache Redis pour optimisation
- Interface d'administration moderne
- Monitoring dashboard avancé
- Déploiement production

### Moyen Terme (6-12 mois)
- Migration microservices progressive
- Message broker (RabbitMQ/Redis)
- Service discovery (Consul)
- Distributed tracing (Jaeger)

### Long Terme (12+ mois)
- Architecture cloud native
- Kubernetes orchestration
- Auto-scaling
- Multi-region deployment

## Contribution

Pour contribuer au projet :

1. **Lire** : [Guide de Développement](development/extending-guide.md)
2. **Comprendre** : [Architecture](architecture/README.md)
3. **Justifier** : [Choix Techniques](technical-decisions/choices-justification.md)
4. **Tester** : Exécuter les tests unitaires
5. **Documenter** : Mettre à jour la documentation

### Standards de Code
- **Style** : Black formatter + Flake8
- **Types** : Type hints obligatoires
- **Tests** : Coverage > 90%
- **Documentation** : Docstrings pour toutes les fonctions publiques

## Support

- **Documentation API** : `/docs` (Swagger) ou `/redoc`
- **Tests** : `pytest tests/ -v`
- **Performance** : `/api/v2/performance/`
- **Santé** : `/api/v2/health/`

---

**FlashNotify** - Système de notification académique moderne, extensible et performant.
