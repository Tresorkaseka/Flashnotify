# Guide de Développement - Système de Notification Académique

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

Ce guide explique comment développer et étendre le système de notification académique. Il s'adresse aux développeurs qui souhaitent:

- Ajouter de nouveaux types de notifications
- Créer de nouveaux canaux de communication
- Personnaliser la logique de priorisation
- Intégrer de nouveaux services externes

### Prérequis

- Python 3.8+
- Connaissance de Flask
- Compréhension des concepts POA (métaclasses, décorateurs, descripteurs)
- Expérience avec SQLAlchemy

---

## Architecture Globale

### Structure du Projet

```
academic-notification-system/
├── core/                       # Composants POA
│   ├── __init__.py
│   ├── metaclasses.py         # NotificationMeta, ChannelMeta
│   ├── decorators.py          # @add_performance_tracking, etc.
│   ├── descriptors.py         # EmailDescriptor, PhoneDescriptor
│   └── notification_system.py # Classes principales
├── models.py                   # Modèles SQLAlchemy
├── app.py                      # Application Flask
├── templates/                  # Templates Jinja2
├── static/                     # CSS, JS
├── tests/                      # Suite de tests
│   ├── conftest.py            # Fixtures pytest
│   ├── test_metaclasses.py
│   ├── test_decorators.py
│   ├── test_descriptors.py
│   ├── test_models.py
│   ├── test_flask_routes.py
│   └── test_integration.py
├── docs/                       # Documentation
│   ├── Points_Discussion_Techniques.md
│   ├── API_Documentation.md
│   ├── Guide_Developpement.md
│   └── Justification_Choix_Techniques.md
├── requirements.txt
├── pytest.ini
└── README.md
```

### Flux de Données

```
[Utilisateur] 
    ↓
[Interface Web/API]
    ↓
[Route Flask] (/send-notification)
    ↓
[NotificationSystem.send()] - Détection du type d'urgence
    ↓
[Notifier Spécifique] (AcademicNotifier, SecurityNotifier, etc.)
    ↓ (apply decorators)
[Performance Tracking] → [Circuit Breaker] → [Validation]
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

#### 4. Mixins

**EmailMixin** - Envoi par email
**SMSMixin** - Envoi par SMS
**PushMixin** - Notifications push

---

## Installation et Configuration

### 1. Installation des Dépendances

```bash
# Cloner le projet
git clone https://github.com/your-org/academic-notification-system.git
cd academic-notification-system

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


# Database
DATABASE_URL=sqlite:///notifications.db


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

#### Étape 2: Ajouter le Type d'Urgence

```python
# core/notification_system.py

class EmergencyType(Enum):
    """Types d'urgence disponibles"""
    WEATHER = "météo"
    SECURITY = "sécurité"
    HEALTH = "santé"
    INFRASTRUCTURE = "infrastructure"
    ACADEMIC = "académique"
    EVENT = "événement"  # ← Nouveau type
```

#### Étape 3: Mapper le Type au Notifieur

```python
# core/notification_system.py

class NotificationSystem:
    TYPE_TO_NOTIFIER = {
        EmergencyType.WEATHER: WeatherNotifier,
        EmergencyType.SECURITY: SecurityNotifier,
        EmergencyType.HEALTH: HealthNotifier,
        EmergencyType.INFRASTRUCTURE: InfrastructureNotifier,
        EmergencyType.ACADEMIC: AcademicNotifier,
        EmergencyType.EVENT: EventNotifier,  # ← Nouveau mapping
    }
```

#### Étape 4: Mettre à Jour le Template

```html
<!-- templates/index.html -->

<select name="emergency_type" required>
    <option value="météo">Météo</option>
    <option value="sécurité">Sécurité</option>
    <option value="santé">Santé</option>
    <option value="infrastructure">Infrastructure</option>
    <option value="académique">Académique</option>
    <option value="événement">Événement</option> <!-- ← Nouveau -->
</select>
```

#### Étape 5: Créer les Tests

```python
# tests/test_notification_system.py

class TestEventNotifier:
    """Tests pour EventNotifier"""
    
    def test_event_notifier_creation(self):
        """Vérifie la création de EventNotifier"""
        notifier = EventNotifier()
        
        assert notifier._notification_type == 'event'
        assert notifier.description == "Notifications pour les événements campus"
    
    def test_event_priority_determination(self):
        """Vérifie la logique de priorisation"""
        notifier = EventNotifier()
        
        priority = notifier.determine_priority(EmergencyType.EVENT)
        assert priority == Priority.LOW
    
    def test_event_channel_selection(self):
        """Vérifie la sélection des canaux"""
        notifier = EventNotifier()
        
        channels = notifier.select_channels({}, Priority.LOW)
        assert 'push' in channels
    
    def test_event_message_customization(self):
        """Vérifie la personnalisation du message"""
        notifier = EventNotifier()
        
        title, body = notifier.customize_message("Conférence", "Détails")
        assert "📅" in title
        assert "Événement Campus" in body
```

### 2. Ajouter un Nouveau Canal de Communication

#### Étape 1: Créer le Mixin

```python
# core/notification_system.py

class WhatsAppMixin(metaclass=ChannelMeta):
    """
    Mixin pour envoyer des notifications via WhatsApp Business API
    """
    
    channel_type = 'whatsapp'
    
    def send_whatsapp(self, user: dict, message: str, title: str) -> dict:
        """
        Envoie une notification via WhatsApp
        
        Args:
            user: Dictionnaire utilisateur avec 'phone'
            message: Corps du message
            title: Titre (ignoré pour WhatsApp)
        
        Returns:
            dict: Résultat de l'envoi
        """
        if 'phone' not in user or not user['phone']:
            return {
                'channel': 'WhatsApp',
                'success': False,
                'error': 'Pas de numéro de téléphone'
            }
        
        try:
            # Mesure de performance
            start_time = time.time()
            
            # Configuration WhatsApp Business API
            import requests
            import os
            
            url = "https://graph.facebook.com/v17.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": user['phone'],
                "type": "text",
                "text": {
                    "body": f"{title}\n\n{message}"
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Tracking de performance
            duration = time.time() - start_time
            self._track_performance(duration, 'send_whatsapp')
            
            # Enregistrement en base
            metric = PerformanceMetric(
                method_name='send_whatsapp',
                duration=duration
            )
            db.session.add(metric)
            db.session.commit()
            
            return {
                'channel': 'WhatsApp',
                'success': True,
                'duration': duration
            }
            
        except Exception as e:
            print(f"Erreur WhatsApp: {str(e)}")
            self.record_failure()
            
            return {
                'channel': 'WhatsApp',
                'success': False,
                'error': str(e)
            }
```

#### Étape 2: Intégrer dans un Notifieur

```python
# core/notification_system.py

class SecurityNotifier(BaseNotifier, EmailMixin, SMSMixin, PushMixin, WhatsAppMixin,
                       metaclass=NotificationMeta):
    """
    Notifieur pour les alertes de sécurité
    Utilise maintenant WhatsApp en plus des autres canaux
    """
    
    def select_channels(self, user: dict, priority: Priority) -> list:
        """
        Sélection des canaux incluant WhatsApp pour les alertes critiques
        """
        if priority == Priority.CRITICAL:
            return ['email', 'sms', 'push', 'whatsapp']  # ← Tous les canaux
        else:
            return ['email', 'push']
```

#### Étape 3: Configuration

```bash
# .env

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_ID=your-phone-number-id
```

### 3. Personnaliser la Logique de Priorisation

#### Exemple: Priorisation Basée sur le Temps

```python
from datetime import datetime

class TimeAwareNotifier(BaseNotifier, EmailMixin, PushMixin, metaclass=NotificationMeta):
    """
    Notifieur qui ajuste la priorité selon l'heure
    """
    
    def determine_priority(self, emergency_type: EmergencyType) -> Priority:
        """
        Augmente la priorité pendant les heures de bureau
        """
        current_hour = datetime.now().hour
        
        # Base priority
        base_priority = super().determine_priority(emergency_type)
        
        # Heures de bureau (8h-18h) = +1 niveau de priorité
        if 8 <= current_hour < 18:
            if base_priority == Priority.LOW:
                return Priority.MEDIUM
            elif base_priority == Priority.MEDIUM:
                return Priority.HIGH
        
        return base_priority
```

#### Exemple: Priorisation Basée sur l'Utilisateur

```python
class RoleBasedNotifier(BaseNotifier, EmailMixin, metaclass=NotificationMeta):
    """
    Notifieur qui priorise selon le rôle de l'utilisateur
    """
    
    def determine_priority(self, emergency_type: EmergencyType, user: dict = None) -> Priority:
        """
        Priorisation basée sur le rôle
        """
        if user and 'role' in user:
            # Administrateurs = priorité maximale
            if user['role'] == 'admin':
                return Priority.CRITICAL
            
            # Professeurs = priorité haute
            elif user['role'] == 'professor':
                return Priority.HIGH
        
        # Priorité normale pour les autres
        return super().determine_priority(emergency_type)
```

### 4. Créer des Descripteurs Personnalisés

#### Exemple: Descripteur pour Valider un Code Postal

```python
# core/descriptors.py

import re

class PostalCodeDescriptor:
    """
    Descripteur pour valider un code postal français
    """
    
    def __init__(self):
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = '_' + name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.name, None)
    
    def __set__(self, instance, value):
        if value is not None:
            # Validation code postal français (5 chiffres)
            if not re.match(r'^\d{5}$', str(value)):
                raise ValueError(f"Code postal invalide: {value}")
        
        setattr(instance, self.name, value)
```

#### Utilisation

```python
# models.py

class Address(db.Model):
    """Modèle d'adresse avec validation"""
    
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    
    # Utilisation du descripteur
    _postal_code = db.Column('postal_code', db.String(5))
    postal_code = PostalCodeDescriptor()
    
    def __init__(self, street, city, postal_code):
        self.street = street
        self.city = city
        self.postal_code = postal_code  # ← Validé automatiquement
```

### 5. Ajouter des Métriques Personnalisées

#### Exemple: Tracking du Taux de Succès

```python
# core/decorators.py

def add_success_rate_tracking(cls):
    """
    Décorateur qui ajoute le tracking du taux de succès
    """
    
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._success_count = 0
        self._failure_count = 0
    
    def get_success_rate(self):
        """Calcule le taux de succès"""
        total = self._success_count + self._failure_count
        if total == 0:
            return 0.0
        return (self._success_count / total) * 100
    
    def record_send_result(self, success: bool):
        """Enregistre le résultat d'un envoi"""
        if success:
            self._success_count += 1
        else:
            self._failure_count += 1
    
    cls.__init__ = new_init
    cls.get_success_rate = get_success_rate
    cls.record_send_result = record_send_result
    
    return cls
```

#### Utilisation

```python
@add_success_rate_tracking
@add_performance_tracking
class AcademicNotifier(BaseNotifier, ...):
    ...
    
    def send_email(self, user, message, title):
        result = super().send_email(user, message, title)
        
        # Enregistrer le résultat
        self.record_send_result(result['success'])
        
        return result

# Plus tard
notifier = AcademicNotifier()
# ... envois de notifications ...
print(f"Taux de succès: {notifier.get_success_rate()}%")
```

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
