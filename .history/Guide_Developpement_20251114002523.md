# Guide de Développement - Système de Notification FlashNotify

## Table des Matières

1. [Introduction](#introduction)
2. [Architecture Globale](#architecture-globale)
3. [Installation et Configuration](#installation-et-configuration)
4. [Étendre le Système](#étendre-le-système)
5. [Bonnes Pratiques](#bonnes-pratiques)
6. [Tests](#tests)
7. [Déploiement](#déploiement)
8. [Résolution de Problèmes](#résolution-de-problèmes)

---

## Introduction

Ce guide explique comment développer et étendre le système de notification FlashNotify. Il s'adresse aux développeurs qui souhaitent:

- Ajouter de nouveaux types de notifications
- Créer de nouveaux canaux de communication
- Personnaliser la logique de priorisation
- Intégrer de nouveaux services externes
- Utiliser les nouvelles fonctionnalités (FastAPI, Auth, Queue, etc.)

### Prérequis

- Python 3.8+
- Connaissance de Flask et FastAPI
- Compréhension des concepts POA (métaclasses, décorateurs, descripteurs)
- Expérience avec SQLAlchemy
- Connaissance de Pydantic pour FastAPI
- Familiarité avec les systèmes de files d'attente (Celery, Redis)

---

## Architecture Globale

### Structure du Projet

```
FlashNotify/
├── api/                        # API FastAPI
│   └── main.py                # Application FastAPI principale
├── core/                       # Composants POA
│   ├── __init__.py
│   ├── metaclasses.py         # NotificationMeta, ChannelMeta, TemplateMeta, ConfigMeta
│   ├── decorators.py          # @add_performance_tracking, etc.
│   ├── descriptors.py         # EmailDescriptor, PhoneDescriptor, PriorityDescriptor, TimeWindowDescriptor
│   ├── notification_system.py # Classes principales
│   ├── auth.py                # Système d'authentification
│   └── queue.py               # Système de files d'attente
├── models.py                   # Modèles SQLAlchemy
├── app.py                      # Application Flask
├── run_fastapi.py              # Script de lancement FastAPI
├── templates/                  # Templates Jinja2
├── static/                     # CSS, JS
├── tests/                      # Suite de tests
│   ├── conftest.py            # Fixtures pytest
│   ├── test_metaclasses.py
│   ├── test_decorators.py
│   ├── test_descriptors.py
│   ├── test_models.py
│   ├── test_flask_routes.py
│   ├── test_fastapi_routes.py
│   └── test_integration.py
├── requirements.txt
├── pytest.ini
└── README.md
```

### Flux de Données

```
[Utilisateur] 
    ↓
[Interface Web/API (Flask/FastAPI)]
    ↓
[Route Flask/FastAPI] (/send-notification)
    ↓
[NotificationSystem.send()] - Détection du type d'urgence
    ↓
[Notifier Spécifique] (AcademicNotifier, SecurityNotifier, etc.)
    ↓ (apply decorators)
[Performance Tracking] → [Circuit Breaker] → [Validation]
    ↓
[Files d'attente] (AsyncQueue, ThreadPoolQueue) ← Nouveau!
    ↓
[Mixins Multi-canaux] (EmailMixin, SMSMixin, PushMixin)
    ↓
[Services Externes] (SMTP, Twilio, Firebase)
    ↓
[Database] (Notification record + PerformanceMetric)
    ↓
[Résultat] → Retour à l'utilisateur
```

### Composants POA Clés

#### 1. Métaclasses

**NotificationMeta** - Génère automatiquement le code pour les notifieurs:
```python
class NotificationMeta(type):
    def __new__(mcs, name, bases, attrs):
        # 1. Génère _notification_type
        # 2. Crée validate_required_fields() automatiquement
        # 3. Enregistre dans NotificationRegistry
        ...
```

**ChannelMeta** - Configure les canaux de communication:
```python
class ChannelMeta(type):
    def __new__(mcs, name, bases, attrs):
        # 1. Génère channel_type
        # 2. Crée get_channel_info()
        ...
```

**TemplateMeta** - Génère des templates de messages (Nouveau!):
```python
class TemplateMeta(type):
    def __new__(mcs, name, bases, attrs):
        # 1. Génère template_version
        # 2. Définit required_variables
        # 3. Crée render_template()
        # 4. Enregistre dans NotificationRegistry
        ...
```

**ConfigMeta** - Gère la configuration dynamique (Nouveau!):
```python
class ConfigMeta(type):
    def __new__(mcs, name, bases, attrs):
        # 1. Ajoute get_config(), set_config()
        # 2. Crée load_from_dict()
        # 3. Implémente Singleton
        # 4. Valide la configuration
        ...
```

#### 2. Décorateurs de Classes

**@add_performance_tracking** - Ajoute le tracking de performance:
- `_track_performance(duration, method)`
- `get_performance_metrics()`
- `get_average_performance()`

**@add_circuit_breaker** - Pattern Circuit Breaker:
- `is_circuit_open()`
- `record_failure()`
- `record_success()`

**@auto_configuration_validation** - Validation automatique à l'initialisation

**@register_in_global_registry** - Enregistrement dans le registre global

#### 3. Descripteurs

**EmailDescriptor** - Validation d'email:
```python
class User:
    email = EmailDescriptor()
    # Valide automatiquement chaque assignation
```

**PhoneDescriptor** - Validation de numéro de téléphone (E.164)

**PriorityDescriptor** - Validation et normalisation de priorité

**TimeWindowDescriptor** - Validation des plages horaires (Nouveau!):
```python
class Notification:
    time_window = TimeWindowDescriptor(start_hour=9, end_hour=17)
    # Valide les plages horaires HH:MM
    # Méthode is_in_window() pour vérifier si l'heure est dans la plage
```

#### 4. Mixins

**EmailMixin** - Envoi par email
**SMSMixin** - Envoi par SMS
**PushMixin** - Notifications push

#### 5. Nouveaux Composants

**Système d'Authentification** - [`core/auth.py`](core/auth.py:1-197):
- Gestion des rôles (Admin, User, API_User)
- Système de permissions granulaires
- Plusieurs méthodes d'authentification (JWT, API Key, Session)
- Hashage sécurisé des mots de passe (SHA256)

**Système de Files d'Attente** - [`core/queue.py`](core/queue.py:1-347):
- **AsyncQueue** - File d'attente asynchrone avec asyncio
- **ThreadPoolQueue** - File d'attente avec ThreadPoolExecutor
- Gestion des priorités et des retries
- Surveillance et logging avancé

**API FastAPI** - [`api/main.py`](api/main.py:1-298):
- Routes complètes pour utilisateurs, notifications et statistiques
- Authentification par token JWT, API Key et sessions
- Validation Pydantic pour toutes les entrées
- Documentation automatique OpenAPI/Swagger

---

## Installation et Configuration

### 1. Installation des Dépendances

```bash
# Cloner le projet
git clone https://github.com/your-org/flashnotify.git
cd flashnotify

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration de la Base de Données

#### Option A: SQLite (Développement)

```python
# app.py (par défaut)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notifications.db'
```

#### Option B: PostgreSQL (Production)

```bash
# Variables d'environnement
export DATABASE_URL="postgresql://user:password@localhost/notifications"
```

```python
# app.py
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///notifications.db'
)
```

### 3. Initialisation de la Base

```python
from app import app, db

with app.app_context():
    db.create_all()
    print("Database initialized!")
```

### 4. Variables d'Environnement

Créer un fichier `.env`:
```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBUG=true

# Database
DATABASE_URL=sqlite:///notifications.db

# Authentification
SESSION_SECRET=your-session-secret-here
JWT_SECRET=your-jwt-secret-here

# Redis (pour les files d'attente)
REDIS_URL=redis://localhost:6379/0

# Celery (pour les tâches asynchrones)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Lancement des Applications

#### Flask (Interface Web)
```bash
python app.py
```

#### FastAPI (API)
```bash
python run_fastapi.py
# ou
uvicorn api.main:app --host 0.0.0 --port 8000 --reload
```

---

## Étendre le Système

### 1. Ajouter un Nouveau Type de Notification

#### Étape 1: Créer la Classe Notifieur

```python
# core/notification_system.py

@add_performance_tracking
@add_circuit_breaker(max_failures=5, timeout=60)
@register_in_global_registry
@auto_configuration_validation
class EventNotifier(BaseNotifier, EmailMixin, PushMixin, metaclass=NotificationMeta):
    """
    Notifieur pour les événements campus (conférences, ateliers, etc.)
    """
    
    # Configuration
    notification_type = 'event'
    description = "Notifications pour les événements campus"
    required_fields = ['email', 'message', 'title']
    
    def determine_priority(self, emergency_type: EmergencyType) -> Priority:
        """
        Logique de priorisation personnalisée pour les événements
        """
        # Événements urgents = MEDIUM, autres = LOW
        if 'urgent' in emergency_type.value.lower():
            return Priority.MEDIUM
        return Priority.LOW
    
    def select_channels(self, user: dict, priority: Priority) -> list:
        """
        Sélection des canaux pour les événements
        """
        channels = []
        
        if priority == Priority.MEDIUM:
            # Événements urgents: email + push
            channels.append('email')
            channels.append('push')
        else:
            # Événements normaux: push seulement
            channels.append('push')
        
        return channels
    
    def customize_message(self, title: str, body: str) -> tuple:
        """
        Personnalisation du message pour les événements
        """
        # Ajouter un emoji et formater le message
        title = f"📅 {title}"
        body = f"Événement Campus:\n\n{body}\n\n---\nNe manquez pas cette opportunité!"
        
        return title, body
```

### 2. Créer un Template de Message

#### Étape 1: Définir un Template avec TemplateMeta

```python
# core/notification_system.py

class EventTemplate(metaclass=TemplateMeta):
    """Template pour les notifications d'événements"""
    
    template_version = '1.0.0'
    required_variables = ['title', 'description', 'date', 'location']
    content = """
    📅 Événement: {{title}}
    📝 Description: {{description}}
    📅 Date: {{date}
    📍 Lieu: {{location}
    """
    
    def __init__(self):
        self.name = "Event Template"
        self.description = "Template pour les notifications d'événements campus"
```

#### Étape 2: Utiliser le Template

```python
# Utilisation dans un notifieur
event_template = EventTemplate()
context = {
    'title': 'Conférence Python',
    'description': 'Apprenez les dernières tendances en Python',
    'date': '2023-12-15',
    'location': 'Salle A101'
}
message = event_template.render_template(context)
```

### 3. Gérer la Configuration Dynamique

#### Étape 1: Créer une Classe de Configuration avec ConfigMeta

```python
# core/config.py

class NotificationConfig(metaclass=ConfigMeta):
    """Configuration pour les notifications"""
    
    required_config_fields = ['smtp_host', 'smtp_port', 'sender_email']
    
    def __init__(self):
        self.set_config('smtp_host', 'smtp.gmail.com')
        self.set_config('smtp_port', 587)
        self.set_config('sender_email', 'no-reply@flashnotify.com')
        self.set_config('max_retries', 3)
        self.set_config('queue_workers', 5)
        self.validate_config()
```

#### Étape 2: Utiliser la Configuration

```python
# Accès à la configuration singleton
config = NotificationConfig()
smtp_host = config.get_config('smtp_host')
max_retries = config.get_config('max_retries', 3)
```

### 4. Utiliser les Files d'Attente

#### Étape 1: Envoi Asynchrone de Notification

```python
# core/queue.py

# Récupération de la file asynchrone globale
from core.queue import async_queue

# Envoi asynchrone d'une notification
task_id = await async_queue.send_notification_async(
    user_id=123,
    title="Notification Importante",
    body="Ceci est un message important",
    emergency_type="sécurité"
)

# Récupération du statut de la tâche
task = async_queue.get_task(task_id)
print(f"Statut: {task.status}, Résultat: {task.result if task.completed_at else 'En cours...'}")
```

### 5. Utiliser l'Authentification

#### Étape 1: Protection des Routes avec JWT

```python
# app.py

from core.auth import require_auth, require_permission, Permission

@app.route('/admin')
@require_auth
@require_permission(Permission.MANAGE_SYSTEM)
def admin_panel():
    """Panneau d'administration protégé"""
    return render_template('admin.html')
```

#### Étape 2: Génération de Tokens

```python
# Génération d'un token JWT
from core.auth import auth_manager

token = auth_manager.generate_jwt_token(user_id=123, role='admin', expires_in_hours=24)
print(f"Token JWT: {token}")

# Validation d'un token
payload = auth_manager.verify_jwt_token(token)
if payload:
    print(f"Utilisateur: {payload['user_id']}, Rôle: {payload['role']}")
```

### 6. Utiliser l'API FastAPI

#### Étape 1: Routes API avec Authentification

```python
# api/main.py

@app.post("/api/v2/notifications/", response_model=Dict[str, Any], tags=["Notifications"])
async def send_notification(notification: NotificationRequest, token: str = Depends(verify_token)):
    """Envoie une notification à un utilisateur"""
    # ... implémentation
```

#### Étape 2: Documentation Interactive

- Accéder à `/docs` pour la documentation Swagger UI
- Accéder à `/redoc` pour la documentation ReDoc
- Les routes sont automatiquement documentées avec exemples

---

## Bonnes Pratiques

### 1. Conventions de Nommage

```python
# Classes
class AcademicNotifier:  # PascalCase
    pass

# Méthodes
def send_notification(self):  # snake_case
    pass

# Constantes
MAX_RETRIES = 3  # UPPER_CASE

# Variables privées
self._internal_state  # préfixe _

# Descripteurs
class EmailDescriptor:  # suffixe Descriptor
    pass

# Mixins
class EmailMixin:  # suffixe Mixin
    pass

# Métaclasses
class TemplateMeta:  # suffixe Meta
    pass
```

### 2. Documentation

```python
def send_notification(self, user: dict, title: str, message: str) -> dict:
    """
    Envoie une notification à un utilisateur.
    
    Args:
        user (dict): Informations utilisateur avec 'email', 'phone', etc.
        title (str): Titre de la notification (max 20 caractères)
        message (str): Corps du message
    
    Returns:
        dict: Résultat de l'envoi avec:
            - 'success' (bool): Succès ou échec
            - 'channels' (list): Canaux utilisés
            - 'duration' (float): Temps d'exécution
    
    Raises:
        ValueError: Si user ou message est invalide
        CircuitBreakerError: Si le circuit est ouvert
    
    Example:
        >>> notifier = AcademicNotifier()
        >>> result = notifier.send_notification(
        ...     {'email': 'test@example.com'},
        ...     'Test',
        ...     'Message de test'
        ... )
        >>> print(result['success'])
        True
    """
    pass
```

### 3. Gestion des Erreurs

```python
def send_email(self, user: dict, message: str, title: str) -> dict:
    """Envoie un email avec gestion d'erreurs robuste"""
    
    # Validation des entrées
    if not user or 'email' not in user:
        return {
            'channel': 'Email',
            'success': False,
            'error': 'Email manquant'
        }
    
    try:
        # Tentative d'envoi
        ...
        
    except smtplib.SMTPAuthenticationError:
        # Erreur d'authentification
        logger.error("Échec d'authentification SMTP")
        self.record_failure()
        return {...}
    
    except smtplib.SMTPException as e:
        # Autres erreurs SMTP
        logger.error(f"Erreur SMTP: {str(e)}")
        self.record_failure()
        return {...}
    
    except Exception as e:
        # Erreurs inattendues
        logger.exception("Erreur inattendue lors de l'envoi d'email")
        self.record_failure()
        return {...}
    
    finally:
        # Nettoyage (fermeture de connexions, etc.)
        pass
```

### 4. Tests

#### Structure de Tests

```python
# tests/test_my_feature.py

class TestMyFeature:
    """Tests pour MyFeature"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        self.notifier = AcademicNotifier()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        pass
    
    def test_basic_functionality(self):
        """Vérifie la fonctionnalité de base"""
        result = self.notifier.some_method()
        assert result is not None
    
    def test_edge_case(self):
        """Vérifie un cas limite"""
        with pytest.raises(ValueError):
            self.notifier.some_method(invalid_input)
    
    def test_integration(self, test_db):
        """Test d'intégration avec la base de données"""
        ...
```

#### Coverage

```bash
# Exécuter les tests avec coverage
pytest --cov=core --cov=models --cov=app --cov-report=html

# Voir le rapport
open htmlcov/index.html
```

### 5. Logging

```python
import logging

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
```python
# Classes
class AcademicNotifier:  # PascalCase
    pass

# Méthodes
def send_notification(self):  # snake_case
    pass

# Constantes
MAX_RETRIES = 3  # UPPER_CASE

# Variables privées
self._internal_state  # préfixe _

# Descripteurs
class EmailDescriptor:  # suffixe Descriptor
    pass

# Mixins
class EmailMixin:  # suffixe Mixin
    pass
```

### 2. Documentation

```python
def send_notification(self, user: dict, title: str, message: str) -> dict:
    """
    Envoie une notification à un utilisateur.
    
    Args:
        user (dict): Informations utilisateur avec 'email', 'phone', etc.
        title (str): Titre de la notification (max 200 caractères)
        message (str): Corps du message
    
    Returns:
        dict: Résultat de l'envoi avec:
            - 'success' (bool): Succès ou échec
            - 'channels' (list): Canaux utilisés
            - 'duration' (float): Temps d'exécution
    
    Raises:
        ValueError: Si user ou message est invalide
        CircuitBreakerError: Si le circuit est ouvert
    
    Example:
        >>> notifier = AcademicNotifier()
        >>> result = notifier.send_notification(
        ...     {'email': 'test@example.com'},
        ...     'Test',
        ...     'Message de test'
        ... )
        >>> print(result['success'])
        True
    """
    pass
```

### 3. Gestion des Erreurs

```python
def send_email(self, user: dict, message: str, title: str) -> dict:
    """Envoie un email avec gestion d'erreurs robuste"""
    
    # Validation des entrées
    if not user or 'email' not in user:
        return {
            'channel': 'Email',
            'success': False,
            'error': 'Email manquant'
        }
    
    try:
        # Tentative d'envoi
        ...
        
    except smtplib.SMTPAuthenticationError:
        # Erreur d'authentification
        logger.error("Échec d'authentification SMTP")
        self.record_failure()
        return {...}
    
    except smtplib.SMTPException as e:
        # Autres erreurs SMTP
        logger.error(f"Erreur SMTP: {str(e)}")
        self.record_failure()
        return {...}
    
    except Exception as e:
        # Erreurs inattendues
        logger.exception("Erreur inattendue lors de l'envoi d'email")
        self.record_failure()
        return {...}
    
    finally:
        # Nettoyage (fermeture de connexions, etc.)
        pass
```

### 4. Tests

#### Structure de Tests

```python
# tests/test_my_feature.py

class TestMyFeature:
    """Tests pour MyFeature"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        self.notifier = AcademicNotifier()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        pass
    
    def test_basic_functionality(self):
        """Vérifie la fonctionnalité de base"""
        result = self.notifier.some_method()
        assert result is not None
    
    def test_edge_case(self):
        """Vérifie un cas limite"""
        with pytest.raises(ValueError):
            self.notifier.some_method(invalid_input)
    
    def test_integration(self, test_db):
        """Test d'intégration avec la base de données"""
        ...
```

#### Coverage

```bash
# Exécuter les tests avec coverage
pytest --cov=core --cov=models --cov=app --cov-report=html

# Voir le rapport
open htmlcov/index.html
```

### 5. Logging

```python
import logging

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Utilisation
logger.debug("Message de debug")
logger.info("Information")
logger.warning("Avertissement")
logger.error("Erreur")
logger.critical("Erreur critique")
```

---

## Tests

### Exécution des Tests

```bash
# Tous les tests
pytest

# Avec verbosité
pytest -v

# Tests spécifiques
pytest tests/test_decorators.py

# Par classe
pytest tests/test_decorators.py::TestCircuitBreakerDecorator

# Par méthode
pytest tests/test_decorators.py::TestCircuitBreakerDecorator::test_circuit_opens_after_max_failures

# Avec coverage
pytest --cov=core --cov-report=term-missing
```

### Debugging des Tests

```python
# Utiliser pdb
import pdb; pdb.set_trace()

# Ou pytest --pdb
pytest --pdb  # S'arrête au premier échec
```

---

## Déploiement

### 1. Préparation

```bash
# Exporter les dépendances
pip freeze > requirements.txt

# Générer une clé secrète
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Production avec Gunicorn

```bash
# Installer Gunicorn
pip install gunicorn

# Lancer l'application
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### 3. Configuration Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/static;
    }
}
```

### 4. Supervisor

```ini
[program:notification-system]
directory=/path/to/app
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/notification-system/err.log
stdout_logfile=/var/log/notification-system/out.log
```

---

## Résolution de Problèmes

### Problème: Circuit Breaker Bloque les Envois

**Symptôme:** Tous les envois échouent avec "Circuit ouvert"

**Solution:**
```python
# Réinitialiser manuellement le circuit
notifier.record_success()

# Ou attendre le timeout (60 secondes par défaut)
```

### Problème: Validation Email Échoue

**Symptôme:** `ValueError: Email invalide`

**Solution:**
```python
# Vérifier le format
import re
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
re.match(pattern, email)

# Nettoyer l'email
email = email.strip().lower()
```

### Problème: Performance Lente

**Symptôme:** Envois prennent >1 seconde

**Diagnostic:**
```python
# Vérifier les métriques
metrics = notifier.get_performance_metrics()
print(f"Moyenne: {notifier.get_average_performance()}s")

# Analyser par méthode
from collections import defaultdict
by_method = defaultdict(list)
for m in metrics:
    by_method[m['method']].append(m['duration'])

for method, durations in by_method.items():
    avg = sum(durations) / len(durations)
    print(f"{method}: {avg:.3f}s")
```

**Solutions:**
- Ajouter un cache Redis
- Utiliser une queue asynchrone (Celery)
- Optimiser les requêtes SQL

### Problème: Tests Échouent

**Symptôme:** `ImportError` ou `ModuleNotFoundError`

**Solution:**
```bash
# Vérifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Réinstaller les dépendances
pip install -r requirements.txt
```

---

## Ressources Supplémentaires

- **Documentation Flask:** https://flask.palletsprojects.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pytest:** https://docs.pytest.org/
- **Python Descriptors:** https://docs.python.org/3/howto/descriptor.html
- **Metaclasses:** https://docs.python.org/3/reference/datamodel.html#metaclasses

---

## Support

Pour toute question ou problème:
- 📧 Email: dev@academic-notifications.edu
- 🐛 Issues: https://github.com/academic-notifications/issues
- 📚 Documentation: https://docs.academic-notifications.edu

Bonne programmation! 🚀
