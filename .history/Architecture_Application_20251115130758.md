
# Architecture de l'Application FlashNotify

## Vue d'Ensemble

FlashNotify est une application de notification académique construite avec Flask et FastAPI. Elle utilise des concepts avancés de Programmation Orientée Aspects (POA) tels que les métaclasses, décorateurs, descripteurs et mixins pour fournir une architecture modulaire, extensible et robuste.

## Composants Principaux

### 1. Core (Cœur de l'Application)

Le module `core` contient les composants principaux de l'application :

- **notification_system.py** : Implémente les notificateurs (AcademicNotifier, SecurityNotifier, etc.) en utilisant des mixins pour les canaux de communication (Email, SMS, Push).
- **metaclasses.py** : Contient les métaclasses (NotificationMeta, ChannelMeta, TemplateMeta, ConfigMeta) pour la génération de code automatique.
- **decorators.py** : Définit des décorateurs de classes pour le suivi des performances, le circuit breaker, la validation de configuration, etc.
- **descriptors.py** : Implémente des descripteurs pour la validation des données (Email, Phone, Priority).
- **auth.py** : Système d'authentification et d'autorisation.
- **queue.py** : Système de files d'attente (AsyncQueue et ThreadPoolQueue) pour l'envoi asynchrone des notifications.

### 2. Modèles (models.py)

Définit les modèles de base de données SQLAlchemy pour les utilisateurs, les notifications et les métriques de performance.

### 3. API (api/main.py)

Implémente une API REST avec FastAPI pour les fonctionnalités avancées de notification, avec authentification JWT, API Key et sessions.

### 4. Application Flask (app.py)

Point d'entrée principal de l'application Flask, gérant les routes web, l'authentification des utilisateurs et l'intégration avec les composants du système de notification.

## Architecture Technique

### 1. Gestion des Notifications

- **Flux de données** : L'utilisateur soumet une notification via l'interface web ou l'API. La notification est placée dans une file d'attente (ThreadPoolQueue). Un worker traite la notification, l'envoie via les canaux appropriés (email, SMS, push) et archive le résultat dans la base de données.
- **Mixins** : Les canaux de communication (EmailMixin, SMSMixin, PushNotificationMixin) sont implémentés comme des mixins pour permettre une composition flexible des notificateurs.
- **Métaclasses** : NotificationMeta génère automatiquement les validateurs de champs requis et enregistre les notificateurs dans un registre global.

### 2. Files d'Attente

- **AsyncQueue** : File d'attente asynchrone basée sur `asyncio`.
