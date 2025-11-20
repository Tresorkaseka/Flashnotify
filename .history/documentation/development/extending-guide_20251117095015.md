# Guide de Développement FlashNotify

## Table des Matières
1. [Introduction](#introduction)
2. [Configuration de l'Environnement](#configuration-de-lenvironnement)
3. [Architecture et Patterns](#architecture-et-patterns)
4. [Étendre le Système](#étendre-le-système)
5. [Ajouter de Nouveaux Canaux](#ajouter-de-nouveaux-canaux)
6. [Créer de Nouveaux Notificateurs](#créer-de-nouveaux-notificateurs)
7. [Bonnes Pratiques](#bonnes-pratiques)
8. [Debugging et Tests](#debugging-et-tests)
9. [Déploiement](#déploiement)

## Introduction

FlashNotify est un système de notification académique basé sur Flask et FastAPI, utilisant des concepts avancés de Programmation Orientée Aspects. Ce guide vous accompagne dans l'extension et la personnalisation du système.

### Prérequis
- Python 3.8+
- Connaissance de Flask/FastAPI
- Compréhension des concepts POO avancés
- Familiarité avec SQLAlchemy

## Configuration de l'Environnement

### Installation des Dépendances
```bash
# Installation des packages requis
pip install -r requirements.txt

# Développement (dépendances supplémentaires)
pip install pytest pytest-cov black flake8 mypy
```

### Configuration de la Base de Données
```bash
# Initialisation de la base de données
python reset_db.py

# Ou manuellement avec Flask
flask init-db
```

### Variables d'Environnement
```bash
# .env
DATABASE_URL=sqlite:///flashnotify.db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

## Architecture et Patterns

### Structure des Modules

```
core/
├── notification_system.py    # Système principal de notification
├── metaclasses.py           # Métaclasses pour auto-configuration
├── decorators.py            # Décorateurs pour fonctionnalités transverses
├── descriptors.py           # Descripteurs pour validation
├── auth.py                  # Système d'authentification
└── queue.py                 # Système de files d'attente

api/
└── main.py                  # API FastAPI

models.py                    # Modèles SQLAlchemy
app.py                       # Application Flask
```

### Patterns Utilisés

#### 1. **Mixin Pattern**
Les mixins permettent la composition de fonctionnalités :
```python
class SMSMixin:
    channel_type = 'sms'
    
    def send_sms(self, message, number):
        # Implémentation SMS
        pass

class EmailMixin:
    channel_type = 'email'
    
    def send_email(self, message, email):
        # Implémentation Email
        pass

# Utilisation
class AcademicNotifier(SMSMixin, EmailMixin):
    pass
```

#### 2. **Decorator Pattern**
Ajout de fonctionnalités transverses :
```python
@add_performance_tracking
@add_circuit_breaker(max_failures=5)
def send_notification(self, data):
    # Méthode avec surveillance automatique
    pass
```

#### 3. **Metaclass Pattern**
Auto-configuration et génération de code :
```python
class NotificationMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Auto-génération de validateurs
        cls._create_validators()
        return cls
```

## Étendre le Système

### Ajout d'un Nouveau Type d'Urgence

1. **Définir le type dans `EmergencyType`** :
```python
from enum import Enum

class EmergencyType(Enum):
    ACADEMIC = "académique"
    WEATHER = "météo"
    SECURITY = "sécurité"
    HEALTH = "santé"
    INFRASTRUCTURE = "infrastructure"
    # Nouveau type
    FINANCIAL = "financier"
```

2. **Mettre à jour la fonction de priorité** :
```python
def get_priority(emergency_type):
    if emergency_type in [EmergencyType.SECURITY, EmergencyType.HEALTH]:
        return Priority.CRITICAL
    elif emergency_type == EmergencyType.WEATHER:
        return Priority.HIGH
    elif emergency_type == EmergencyType.FINANCIAL:  # Nouveau
        return Priority.HIGH
    # ...
```

3. **Tester le nouveau type** :
```python
def test_financial_emergency():
    notifier = AcademicNotifier()
    result = notifier.notify(
        user=user_data,
        title="Alerte Financière",
        body="Budget dépassé de 20%",
        emergency_type=EmergencyType.FINANCIAL
    )
    assert result['priority'] == Priority.HIGH.name
```

## Ajouter de Nouveaux Canaux

### Canal Slack

1. **Créer le mixin Slack** :
```python
class SlackMixin:
    channel_type = 'slack'
    
    def __init__(self):
        self.slack_client = SlackClient(os.getenv('SLACK_TOKEN'))
    
    @log_notification
    @retry_on_failure(retries=3)
    def send_slack(self, message, channel):
        """Envoie une notification vers Slack"""
        try:
            result = self.slack_client.api_call(
                'chat.postMessage',
                channel=channel,
                text=message,
                username='FlashNotify Bot'
            )
            return {
                'status': 'success',
                'channel': 'Slack',
                'recipient': channel,
                'message': message
            }
        except Exception as e:
            raise Exception(f"Échec d'envoi Slack: {e}")
```

2. **Intégrer dans un notificateur** :
```python
class AcademicNotifier(SMSMixin, EmailMixin, PushNotificationMixin, 
                       SlackMixin, FormattingMixin, ArchiveMixin, 
                       UserPreferenceMixin, metaclass=NotificationMeta):
    
    def send_all_channels(self, message, user):
        results = []
        # ... autres canaux ...
        
        # Ajouter Slack
        if user.get('slack_channel'):
            try:
                results.append(self.send_slack(message, user['slack_channel']))
            except Exception as e:
                print(f"Erreur Slack: {e}")
        
        return results
```

### Canal Discord

1. **Mixin Discord** :
```python
class DiscordMixin:
    channel_type = 'discord'
    
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    @log_notification
    @retry_on_failure(retries=3)
    def send_discord(self, message, username="FlashNotify"):
        """Envoie une notification vers Discord via webhook"""
        try:
            data = {
                'content': message,
                'username': username,
                'embeds': [{
                    'title': 'Notification FlashNotify',
                    'description': message,
                    'color': 0x00ff00,
                    'timestamp': datetime.utcnow().isoformat()
                }]
            }
            
            response = requests.post(self.webhook_url, json=data)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'channel': 'Discord',
                'recipient': 'webhook',
                'message': message
            }
        except Exception as e:
            raise Exception(f"Échec d'envoi Discord: {e}")
```

## Créer de Nouveaux Notificateurs

### Notificateur Médical

```python
@add_performance_tracking
@auto_configuration_validation
@register_in_global_registry
@add_circuit_breaker(max_failures=3, timeout=30)
class MedicalNotifier(SMSMixin, EmailMixin, PushNotificationMixin,
                      ArchiveMixin, metaclass=NotificationMeta):
    """Notificateur spécialisé pour les urgences médicales"""
    
    required_fields = ['hospital_code', 'emergency_level']
    description = "Système de notification médicale"
    
    def __init__(self):
        self._notification_type = 'medical'
        self.hospital_codes = self._load_hospital_codes()
    
    def notify_medical_emergency(self, patient_data, emergency_type, level):
        """Notification d'urgence médicale avec protocole spécifique"""
        
        # Priorité basée sur le niveau d'urgence
        if level in ['critical', 'urgent']:
            priority = Priority.CRITICAL
        elif level == 'moderate':
            priority = Priority.HIGH
        else:
            priority = Priority.MEDIUM
        
        # Message formaté selon le protocole médical
        message = self._format_medical_message(
            patient_data, emergency_type, level
        )
        
        # Envoi sur canaux multiples pour les urgences critiques
        if priority == Priority.CRITICAL:
            results = self.send_all_channels(message, patient_data)
            
            # Notification aux équipes médicales
            for team in self.get_medical_teams(patient_data['hospital_code']):
                self.notify_team(team, message, priority)
        else:
            results = self.send_preferred_channel(message, patient_data)
        
        # Archivage avec données médicales
        notification_data = {
            'patient_id': patient_data['id'],
            'hospital_code': patient_data['hospital_code'],
            'emergency_level': level,
            'message': message,
            'priority': priority,
            'results': results
        }
        
        return self.archive_medical_notification(notification_data)
    
    def _format_medical_message(self, patient_data, emergency_type, level):
        """Formatage spécifique aux messages médicaux"""
        return (
            f"[URGENCE MÉDICALE - {level.upper()}]\n"
            f"Patient: {patient_data['name']} (ID: {patient_data['id']})\n"
            f"Type: {emergency_type}\n"
            f"Hôpital: {patient_data['hospital_code']}\n"
            f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
```

### Notificateur d'Urgence Civile

```python
class CivilEmergencyNotifier(EmailMixin, SMSMixin, PushNotificationMixin,
                            FormattingMixin, ArchiveMixin,
                            metaclass=NotificationMeta):
    """Notificateur pour les urgences civiles et catastrophes"""
    
    def __init__(self):
        self._notification_type = 'civil_emergency'
        self.alert_levels = {
            'green': Priority.LOW,
            'yellow': Priority.MEDIUM,
            'orange': Priority.HIGH,
            'red': Priority.CRITICAL
        }
    
    def send_civil_alert(self, location, alert_level, message):
        """Envoi d'alerte civile par zone géographique"""
        
        # Récupération des utilisateurs par zone
        affected_users = self.get_users_by_location(location)
        
        priority = self.alert_levels.get(alert_level, Priority.MEDIUM)
        formatted_message = self._format_civil_message(message, location, alert_level)
        
        results = []
        for user in affected_users:
            user_result = self.notify_user(user, formatted_message, priority)
            results.append(user_result)
        
        return {
            'location': location,
            'alert_level': alert_level,
            'affected_users': len(affected_users),
            'results': results
        }
```

## Bonnes Pratiques

### 1. **Validation des Données**
Toujours valider les données avec les descripteurs :
```python
class User(db.Model):
    _email = EmailDescriptor()
    _phone = PhoneDescriptor()
    
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        self._email = value  # Validation automatique
```

### 2. **Gestion des Erreurs**
Utiliser les décorateurs appropriés :
```python
@add_circuit_breaker(max_failures=5)
@add_performance_tracking
@retry_on_failure(retries=3)
def send_notification(self, data):
    try:
        # Logique d'envoi
        pass
    except SpecificException as e:
        # Gestion spécifique
        raise
    except Exception as e:
        # Gestion générale
        self.log_error(e)
        raise
```

### 3. **Configuration**
Utiliser la métaclasse de configuration :
```python
@auto_configuration_validation
class NotificationConfig:
    max_retries = 3
    timeout = 60
    
    def validate(self):
        # Validation automatique des paramètres
        pass
```

### 4. **Tests**
Créer des tests pour chaque extension :
```python
class TestSlackMixin:
    def setup_method(self):
        self.mixin = SlackMixin()
        self.test_user = {'slack_channel': '#alerts'}
    
    def test_send_slack_success(self):
        # Test d'envoi réussi
        result = self.mixin.send_slack("Test message", "#alerts")
        assert result['status'] == 'success'
    
    def test_send_slack_failure(self):
        # Test de gestion d'échec
        with pytest.raises(Exception):
            self.mixin.send_slack("Test", "#invalid")
```

## Debugging et Tests

### Debugging des Notifications

1. **Activer le mode debug** :
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Dans votre code
logger = logging.getLogger(__name__)
logger.debug(f"Envoi notification: {data}")
```

2. **Utiliser les métriques de performance** :
```python
# Vérifier les performances
metrics = PerformanceMetric.query.filter_by(
    method_name='send_email'
).all()

for metric in metrics:
    print(f"Durée: {metric.execution_time}s, Succès: {metric.success}")
```

3. **Tester le circuit breaker** :
```python
# Simuler des échecs pour tester le circuit breaker
notifier = AcademicNotifier()

# Le circuit s'ouvre après 5 échecs
for i in range(6):
    try:
        notifier.notify(test_user, "Test", "Message")
    except Exception as e:
        print(f"Échec {i+1}: {e}")

# Vérifier l'état du circuit
print(f"Circuit ouvert: {notifier.is_circuit_open()}")
```

### Tests Automatisés

1. **Tests unitaires** :
```bash
# Lancer les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=core --cov-report=html
```

2. **Tests d'intégration API** :
```python
def test_send_notification_api(client, auth_headers):
    response = client.post('/api/v2/notifications/', 
                          json={
                              'user_email': 'test@example.com',
                              'title': 'Test Alert',
                              'body': 'Test message'
                          },
                          headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'notification_id' in data
```

3. **Tests de charge** :
```python
import asyncio
import aiohttp

async def stress_test_notifications():
    """Test de charge pour l'API"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = send_notification_async(session, i)
            tasks.append(task)
        
        await asyncio.gather(*tasks)

# Exécuter
asyncio.run(stress_test_notifications())
```

## Déploiement

### Configuration Production

1. **Variables d'environnement** :
```bash
# Production
export DATABASE_URL=postgresql://user:pass@localhost/flashnotify
export SECRET_KEY=prod-secret-key
export JWT_SECRET_KEY=prod-jwt-secret
export DEBUG=False
export LOG_LEVEL=INFO
```

2. **WSGI Configuration** (Gunicorn) :
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()" --timeout 60
```

3. **Docker** :
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```

### Monitoring

1. **Métriques de performance** :
```python
# Surveillance automatique
@app.route('/admin/metrics')
@admin_required
def performance_metrics():
    metrics = PerformanceMetric.query.filter(
        PerformanceMetric.created_at > datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    return render_template('metrics.html', metrics=metrics)
```

2. **Alertes** :
```python
# Configuration d'alertes
def check_system_health():
    failure_rate = calculate_failure_rate()
    if failure_rate > 0.1:  # 10% d'échecs
        send_admin_alert(f"Taux d'échec élevé: {failure_rate:.2%}")
```

### Sauvegarde

1. **Base de données** :
```bash
# Sauvegarde quotidienne
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump flashnotify > backup_$DATE.sql

# Nettoyage (garder 30 jours)
find /backups -name "backup_*.sql" -mtime +30 -delete
```

2. **Logs** :
```bash
# Rotation des logs
logrotate /etc/logrotate.d/flashnotify
```

Ce guide vous donne les bases pour étendre et maintenir FlashNotify. Pour des questions spécifiques, consultez la documentation de l'API ou les tests existants.
