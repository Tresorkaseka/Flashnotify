# Système de Notification FlashNotify

Application web Flask et FastAPI démontrant l'utilisation de concepts POO avancés en Python : **Décorateurs de classes**, **Descripteurs** et **Métaclasses** avec intégration d'un système d'authentification, de files d'attente asynchrones et d'une API moderne.

## 📋 Vue d'ensemble

Ce projet est un système de notification complet qui permet d'envoyer des notifications par différents canaux (Email, SMS, Push) selon le type d'urgence et les préférences utilisateur. L'application utilise Flask pour l'interface web, FastAPI pour l'API moderne, PostgreSQL pour la base de données, et démontre l'utilisation de concepts POO avancés pour améliorer la maintenabilité et l'extensibilité du code. Le système inclut également une authentification sécurisée, un système de files d'attente asynchrone et une documentation API complète.

## 🎯 Concepts POO Avancés Implémentés

### 1. Décorateurs de Classes

Les décorateurs de classes ajoutent des fonctionnalités transversales sans modifier le code existant.

**Fichier : `core/decorators.py`**

#### `@add_performance_tracking`
- Ajoute automatiquement le suivi des performances à chaque envoi de notification
- Enregistre la durée d'exécution de chaque méthode
- Calcule les moyennes de performance

#### `@auto_configuration_validation`
- Valide automatiquement la configuration au moment de l'instanciation
- Vérifie que tous les champs requis sont présents

#### `@register_in_global_registry`
- Enregistre automatiquement la classe dans un registre global
- Permet la découverte automatique des notificateurs

#### `@add_circuit_breaker`
- Implémente le pattern Circuit Breaker
- Gère automatiquement les pannes en ouvrant le circuit après trop d'échecs
- Se réinitialise automatiquement après un timeout

**Exemple d'utilisation :**
```python
@add_performance_tracking
@auto_configuration_validation
@register_in_global_registry
@add_circuit_breaker(max_failures=5, timeout=60)
class AcademicNotifier:
    # La classe bénéficie automatiquement de toutes ces fonctionnalités
    pass
```

### 2. Descripteurs

Les descripteurs permettent de contrôler l'accès aux attributs et de valider automatiquement les données.

**Fichier : `core/descriptors.py`**

#### `EmailDescriptor`
- Valide automatiquement le format email lors de l'affectation
- Utilise une regex pour vérifier la présence de @ et d'un domaine valide
- Lève une `ValueError` si l'email est invalide

#### `PhoneDescriptor`
- Valide les numéros de téléphone internationaux
- Format requis : +[code pays][numéro] (ex: +33612345678)
- Supporte entre 7 et 15 chiffres

#### `PriorityDescriptor`
- Contrôle les niveaux de priorité (LOW, MEDIUM, HIGH, CRITICAL)
- Convertit automatiquement en majuscules
- Valeur par défaut : MEDIUM

#### `TimeWindowDescriptor` - Nouveau!
- Valide les plages horaires au format HH:MM
- Méthode `is_in_window()` pour vérifier si l'heure est dans la plage définie
- Support des plages chevauchant minuit

**Exemple d'utilisation :**
```python
class User:
    email = EmailDescriptor()
    phone = PhoneDescriptor()
    time_preference = TimeWindowDescriptor(start_hour=9, end_hour=17)
    
    def __init__(self, email, phone):
        self.email = email  # Validation automatique ici
        self.phone = phone  # Validation automatique ici
        self.time_preference = {'start': '09:00', 'end': '17:00'}  # Validation automatique
```

### 3. Métaclasses

Les métaclasses génèrent automatiquement du code lors de la création des classes.

**Fichier : `core/metaclasses.py`**

#### `NotificationMeta`
- Génère automatiquement une méthode `validate_required_fields()` basée sur l'attribut `required_fields`
- Ajoute automatiquement une description si non fournie
- Enregistre la classe dans le `NotificationRegistry`
- Définit le type de notification automatiquement

#### `ChannelMeta`
- Génère automatiquement le type de canal basé sur le nom de la classe
- Ajoute une méthode `get_channel_info()` pour récupérer les informations du canal

#### `TemplateMeta` - Nouveau!
- Génère des templates de messages avec variables requises
- Méthode `render_template()` pour substitution de variables
- Enregistrement automatique dans le registre global

#### `ConfigMeta` - Nouveau!
- Gère la configuration dynamique avec pattern Singleton
- Méthodes `get_config()`, `set_config()`, `load_from_dict()`
- Validation automatique de la configuration

**Exemple d'utilisation :**
```python
class WeatherAlert(metaclass=NotificationMeta):
    required_fields = ['location', 'severity', 'effective_time']
    # La méthode validate_required_fields() est générée automatiquement

class EventTemplate(metaclass=TemplateMeta):
    required_variables = ['title', 'date', 'location']
    content = "Événement: {{title}} le {{date}} à {{location}}"
    # La méthode render_template() est générée automatiquement
```

## 🔧 Fonctionnalités Avancées

### 1. Système d'Authentification et Autorisation
**Fichier : `core/auth.py`**

- Gestion des rôles (Admin, User, API_User)
- Système de permissions granulaires
- Plusieurs méthodes d'authentification (JWT, API Key, Session)
- Hashage sécurisé des mots de passe (SHA256)

### 2. Système de Files d'Attente Asynchrones
**Fichier : `core/queue.py`**

- **AsyncQueue** - File d'attente asynchrone avec asyncio
- **ThreadPoolQueue** - File d'attente avec ThreadPoolExecutor
- Gestion des priorités et des retries
- Surveillance et logging avancé

### 3. API Modernes avec FastAPI
**Fichier : `api/main.py`**

- Routes complètes pour utilisateurs, notifications et statistiques
- Authentification par token JWT, API Key et sessions
- Validation Pydantic pour toutes les entrées
- Documentation automatique OpenAPI/Swagger

## 🏗️ Architecture du Projet

```
.
├── app.py                          # Application Flask principale
├── run_fastapi.py                  # Script de lancement FastAPI
├── models.py                       # Modèles de base de données SQLAlchemy
├── requirements.txt                # Dépendances Python
├── core/                           # Module des concepts POO avancés
│   ├── __init__.py
│   ├── decorators.py              # Décorateurs de classes
│   ├── descriptors.py             # Descripteurs de validation
│   ├── metaclasses.py             # Métaclasses pour génération de code
│   ├── auth.py                    # Système d'authentification
│   ├── queue.py                   # Système de files d'attente
│   └── notification_system.py     # Système de notification avec mixins
├── api/                            # API FastAPI
│   └── main.py                    # Application FastAPI principale
├── templates/                      # Templates HTML Jinja2
│   ├── base.html                  # Template de base
│   ├── index.html                 # Page d'envoi de notifications
│   ├── dashboard.html             # Dashboard des notifications
│   └── admin.html                 # Administration des utilisateurs
└── static/
    └── css/
        └── style.css              # Styles CSS personnalisés
```

## 🔧 Fonctionnalités

### 1. Système de Notification Multi-Canal

- **Email** : Simulation d'envoi d'emails
- **SMS** : Simulation d'envoi de SMS
- **Push** : Simulation de notifications push

### 2. Gestion des Priorités

Les priorités sont déterminées automatiquement selon le type d'urgence :

- **CRITICAL** : Sécurité, Santé → Envoi sur tous les canaux
- **HIGH** : Météo → Envoi selon préférences utilisateur
- **MEDIUM** : Infrastructure → Envoi selon préférences utilisateur
- **LOW** : Académique → Envoi selon préférences utilisateur

### 3. Types d'Urgences

- 🌩️ **Météo** : Alertes météorologiques
- 🚨 **Sécurité** : Alertes de sécurité critiques
- 🏥 **Santé** : Alertes sanitaires
- 🔧 **Infrastructure** : Problèmes d'infrastructure
- 📚 **Académique** : Notifications académiques

### 4. Interface Web

- **Page d'envoi** : Formulaire pour envoyer des notifications
- **Dashboard** : Visualisation des notifications avec statistiques et filtres
- **Administration** : Gestion des utilisateurs avec validation automatique

### 5. API RESTful avec FastAPI

- Endpoints pour la gestion des utilisateurs
- Endpoints pour l'envoi et la gestion des notifications
- Endpoints pour les statistiques et métriques
- Documentation interactive Swagger UI

## 🚀 Installation et Utilisation

### Prérequis

- Python 3.11
- PostgreSQL ou SQLite
- Variables d'environnement configurées

### Installation

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

### Configuration

Créer un fichier `.env` avec les variables suivantes :
```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Database
DATABASE_URL=sqlite:///notifications.db

# Authentification
SESSION_SECRET=votre_cle_secrete
JWT_SECRET=votre_jwt_secret

# Redis (pour les files d'attente)
REDIS_URL=redis://localhost:6379/0
```

### Démarrage

Lancer l'application Flask (interface web) :
```bash
python app.py
```

Lancer l'API FastAPI :
```bash
python run_fastapi.py
# ou
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

L'application initialise automatiquement :
- La base de données
- Les tables (users, notifications, performance_metrics)
- 3 utilisateurs de test :
  - Alice Martin (alice.martin@universite.edu) - Préfère Email
  - Bob Dupont (bob.dupont@universite.edu) - Préfère Push
  - Charlie Bernard (charlie.bernard@universite.edu) - Préfère Email

### Utilisation

1. **Envoyer une notification via l'interface web** : 
   - Aller sur la page d'accueil
   - Sélectionner un utilisateur
   - Choisir le type d'urgence (la priorité est automatique)
   - Remplir le titre et le message
   - Cliquer sur "Envoyer la Notification"

2. **Utiliser l'API FastAPI** :
   - Accéder à http://localhost:8000/docs pour la documentation interactive
   - Utiliser les endpoints pour gérer les notifications par programme
   - Authentification requise pour la plupart des endpoints

3. **Voir le dashboard** :
   - Cliquer sur "Dashboard" dans la navigation
   - Voir les statistiques globales
   - Filtrer par type ou priorité
   - Consulter l'historique complet

4. **Gérer les utilisateurs** :
   - Cliquer sur "Admin" dans la navigation
   - Ajouter un utilisateur (validation automatique email/téléphone)
   - Voir la liste des utilisateurs
   - Supprimer un utilisateur

## 📊 Base de Données

### Modèle User
```python
- id: Integer (clé primaire)
- name: String(100)
- email: String(120) - Validé par EmailDescriptor
- phone: String(20) - Validé par PhoneDescriptor
- prefers_email: Boolean - Préférence de canal
- created_at: DateTime
```

### Modèle Notification
```python
- id: Integer (clé primaire)
- user_id: Integer (clé étrangère)
- title: String(200)
- body: Text
- emergency_type: String(50)
- priority: String(20) - Validé par PriorityDescriptor
- channels: String(200) - Canaux utilisés
- status: String(20)
- created_at: DateTime
```

### Modèle PerformanceMetric
```python
- id: Integer (clé primaire)
- method_name: String(100)
- duration: Float - Durée en secondes
- timestamp: DateTime
```

## 🎨 Design Patterns Utilisés

1. **Mixin Pattern** : SMSMixin, EmailMixin, PushNotificationMixin
2. **Decorator Pattern** : Décorateurs de fonctions et de classes
3. **Registry Pattern** : NotificationRegistry pour enregistrer les notificateurs
4. **Circuit Breaker Pattern** : Gestion automatique des pannes
5. **Template Method Pattern** : Templates HTML avec Jinja2
6. **Singleton Pattern** : ConfigMeta
7. **Observer Pattern** : Système de notifications

## 🔍 Validation des Données

La validation est effectuée à plusieurs niveaux :

1. **Au niveau du formulaire** : Validation HTML5 côté client
2. **Au niveau des descripteurs** : Validation automatique lors de l'affectation
3. **Au niveau de la base de données** : Contraintes NOT NULL et UNIQUE
4. **Au niveau de l'API** : Validation Pydantic pour FastAPI

### Exemples de validation

**Email valide** : `etudiant@universite.edu` ✅  
**Email invalide** : `etudiant.com` ❌

**Téléphone valide** : `+33612345678` ✅  
**Téléphone invalide** : `123456` ❌

**Priorité valide** : `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` ✅  
**Priorité invalide** : `SUPER_HIGH` ❌

**Plage horaire valide** : `{'start': '09:00', 'end': '17:00'}` ✅
**Plage horaire invalide** : `{'start': '25:00', 'end': '17:00'}` ❌

## 🧪 Tests et Démonstration

### Tester l'envoi de notifications

1. Envoyez une notification de type "Sécurité" → Observez l'envoi sur tous les canaux (CRITICAL)
2. Envoyez une notification de type "Académique" → Observez l'envoi selon les préférences (LOW)
3. Consultez le dashboard pour voir les statistiques mises à jour

### Tester la validation

1. Essayez d'ajouter un utilisateur avec un email invalide → Erreur de validation
2. Essayez d'ajouter un utilisateur avec un téléphone invalide → Erreur de validation
3. Les descripteurs protègent l'intégrité des données

### Tester le Circuit Breaker

Le système simule aléatoirement des échecs d'envoi (10% de chance). Si trop d'échecs se produisent, le circuit s'ouvre automatiquement pour protéger le système.

### Tester l'API FastAPI

1. Accéder à http://localhost:8000/docs
2. Tester les endpoints avec la documentation interactive
3. Authentifier avec un token JWT ou une API Key
4. Envoyer des notifications via l'API

## 📚 Justification des Choix Techniques

### Pourquoi les Décorateurs de Classes ?

- **Réutilisabilité** : Ajout de fonctionnalités sans modifier les classes
- **Séparation des préoccupations** : Code métier séparé du code transversal
- **Maintenabilité** : Facile d'ajouter/retirer des fonctionnalités

### Pourquoi les Descripteurs ?

- **Validation centralisée** : Une seule implémentation pour tous les usages
- **Réutilisabilité** : Mêmes descripteurs pour plusieurs classes
- **Encapsulation** : Logique de validation cachée dans le descripteur

### Pourquoi les Métaclasses ?

- **Génération de code** : Création automatique de méthodes répétitives
- **Convention over Configuration** : Comportement automatique basé sur les conventions
- **DRY (Don't Repeat Yourself)** : Évite la duplication de code

### Pourquoi Flask et FastAPI ?

- **Flask** : Simplicité et flexibilité pour l'interface web
- **FastAPI** : Performance et documentation automatique pour l'API
- **Complémentarité** : Interface utilisateur avec Flask, API moderne avec FastAPI

### Pourquoi les files d'attente ?

- **Performance** : Traitement asynchrone des notifications
- **Fiabilité** : Gestion des erreurs et retries
- **Évolutivité** : Capacité à gérer un grand volume de notifications

## 🔄 Extensibilité

Le système est conçu pour être facilement extensible :

1. **Ajouter un nouveau canal** :
   ```python
   class SlackMixin(metaclass=ChannelMeta):
       def send_slack(self, message, channel):
           # Implémentation
   ```

2. **Ajouter un nouveau type d'urgence** :
   ```python
   class EmergencyType(Enum):
       NEW_TYPE = "nouveau_type"
   ```

3. **Ajouter un nouveau descripteur** :
   ```python
   class URLDescriptor:
       def __set__(self, instance, value):
           # Validation URL
   ```

4. **Créer un template personnalisé** :
   ```python
   class CustomTemplate(metaclass=TemplateMeta):
       required_variables = ['user_name', 'event_name']
       content = "Bonjour {{user_name}}, l'événement {{event_name}}..."
   ```

## 🎓 Valeur Pédagogique

Ce projet démontre :

- L'utilisation pratique de concepts POO avancés
- L'intégration de ces concepts dans une application réelle
- Les avantages de la programmation orientée objet pour la maintenabilité
- Les patterns de conception modernes en Python
- L'architecture d'une application web complète avec API et authentification
- L'utilisation de systèmes de files d'attente pour le traitement asynchrone

## 📝 Notes Importantes

- Les envois de notifications sont **simulés** (pas d'intégration réelle SMS/Email)
- La base de données peut être PostgreSQL ou SQLite en développement
- L'application utilise Flask en mode debug (à ne pas utiliser en production)
- Les descripteurs sont utilisés via des fonctions de validation compatibles avec SQLAlchemy
- L'API FastAPI fournit une documentation interactive et des validations automatiques

## 🤝 Auteur

Projet étudiant - Système de Notification FlashNotify  
Framework : Flask + FastAPI + PostgreSQL  
Concepts : POO Avancée (Décorateurs, Descripteurs, Métaclasses), Authentification, Files d'attente, API moderne

---

**Note** : Ce projet est conçu à des fins pédagogiques pour démontrer l'utilisation de concepts POO avancés en Python dans un contexte d'application web réelle avec des fonctionnalités modernes.
