# Documentation API - Système de Notification Académique

## OpenAPI/Swagger Specification

```yaml
openapi: 3.0.3
info:
  title: Système de Notification Académique
  description: |
    API REST pour gérer les notifications académiques avec support multi-canaux (Email, SMS, Push).
    
    ## Fonctionnalités
    - Envoi de notifications multi-canaux
    - Gestion des utilisateurs
    - Dashboard avec statistiques
    - Métriques de performance
    - Priorisation automatique selon le type d'urgence
    
    ## Concepts POA Implémentés
    - **Décorateurs de classes**: Performance tracking, Circuit breaker
    - **Métaclasses**: Génération automatique de code, Registry pattern
    - **Mixins**: Multi-channel notification
    - **Descripteurs**: Validation des données
  version: 1.0.0
  contact:
    name: Support Technique
    email: support@academic-notifications.edu

servers:
  - url: http://localhost:5000
    description: Serveur de développement
  - url: https://api.academic-notifications.edu
    description: Serveur de production

tags:
  - name: Notifications
    description: Opérations sur les notifications
  - name: Utilisateurs
    description: Gestion des utilisateurs
  - name: Statistiques
    description: Statistiques et métriques
  - name: API
    description: Endpoints API REST

paths:
  /:
    get:
      summary: Page d'accueil
      description: Affiche le formulaire d'envoi de notification
      tags:
        - Notifications
      responses:
        '200':
          description: Page d'accueil chargée avec succès
          content:
            text/html:
              schema:
                type: string
  
  /send-notification:
    post:
      summary: Envoyer une notification
      description: |
        Envoie une notification à un utilisateur selon le type d'urgence sélectionné.
        
        **Comportement selon priorité:**
        - **CRITICAL** (Sécurité, Santé): Email + SMS + Push
        - **HIGH** (Météo): Email ou Push selon préférence
        - **MEDIUM** (Infrastructure): Email ou Push selon préférence
        - **LOW** (Académique): Email ou Push selon préférence
        
        **Circuit Breaker:**
        - Si >5 échecs en 60 secondes, le circuit s'ouvre
        - Les envois sont bloqués jusqu'à récupération
      tags:
        - Notifications
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required:
                - user_id
                - title
                - body
                - emergency_type
              properties:
                user_id:
                  type: integer
                  description: ID de l'utilisateur destinataire
                  example: 1
                title:
                  type: string
                  description: Titre de la notification
                  maxLength: 200
                  example: "Alerte Académique"
                body:
                  type: string
                  description: Corps du message
                  example: "Rappel: Examen demain à 9h"
                emergency_type:
                  type: string
                  enum:
                    - météo
                    - sécurité
                    - santé
                    - infrastructure
                    - académique
                  description: Type d'urgence (détermine la priorité)
                  example: "académique"
      responses:
        '302':
          description: Redirection après envoi
          headers:
            Location:
              schema:
                type: string
              description: URL de redirection (généralement '/')
        '200':
          description: Page avec message de succès/erreur
          content:
            text/html:
              schema:
                type: string
  
  /dashboard:
    get:
      summary: Dashboard des notifications
      description: Affiche toutes les notifications avec filtres et statistiques
      tags:
        - Notifications
        - Statistiques
      parameters:
        - name: type
          in: query
          description: Filtrer par type d'urgence
          required: false
          schema:
            type: string
            enum:
              - météo
              - sécurité
              - santé
              - infrastructure
              - académique
        - name: priority
          in: query
          description: Filtrer par priorité
          required: false
          schema:
            type: string
            enum:
              - LOW
              - MEDIUM
              - HIGH
              - CRITICAL
      responses:
        '200':
          description: Dashboard chargé avec succès
          content:
            text/html:
              schema:
                type: string
  
  /admin:
    get:
      summary: Page d'administration
      description: Gestion des utilisateurs
      tags:
        - Utilisateurs
      responses:
        '200':
          description: Page admin chargée
          content:
            text/html:
              schema:
                type: string
  
  /admin/add-user:
    post:
      summary: Ajouter un utilisateur
      description: |
        Crée un nouvel utilisateur avec validation des données.
        
        **Validations:**
        - Email: Format RFC 5322
        - Téléphone: Format international E.164 (optionnel)
        - Nom: Requis, 2-100 caractères
      tags:
        - Utilisateurs
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required:
                - name
                - email
              properties:
                name:
                  type: string
                  minLength: 2
                  maxLength: 100
                  description: Nom complet de l'utilisateur
                  example: "Alice Martin"
                email:
                  type: string
                  format: email
                  description: Adresse email (validée via descripteur)
                  example: "alice.martin@universite.edu"
                phone:
                  type: string
                  pattern: '^\+?[1-9]\d{1,14}$'
                  description: Numéro de téléphone international (optionnel)
                  example: "+33612345678"
                prefers_email:
                  type: string
                  enum: ['on']
                  description: Présent si l'utilisateur préfère email (checkbox)
      responses:
        '302':
          description: Redirection vers /admin après ajout
        '200':
          description: Page avec message d'erreur si validation échoue
  
  /admin/delete-user/{user_id}:
    post:
      summary: Supprimer un utilisateur
      description: |
        Supprime un utilisateur et toutes ses notifications (cascade).
        
        **Cascade Delete:**
        - Utilisateur
        - Toutes les notifications associées
      tags:
        - Utilisateurs
      parameters:
        - name: user_id
          in: path
          required: true
          description: ID de l'utilisateur à supprimer
          schema:
            type: integer
            example: 1
      responses:
        '302':
          description: Redirection vers /admin après suppression
        '200':
          description: Page avec message d'erreur si utilisateur introuvable
  
  /api/notifications:
    get:
      summary: Liste des notifications (API)
      description: |
        Retourne les 50 dernières notifications au format JSON.
        
        **Utilisation:**
        - Intégration avec applications tierces
        - Dashboard externe
        - Monitoring
      tags:
        - API
      responses:
        '200':
          description: Liste des notifications
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Notification'
              example:
                - id: 1
                  user_id: 1
                  user_name: "Alice Martin"
                  title: "Alerte Académique"
                  body: "Examen demain"
                  emergency_type: "académique"
                  priority: "LOW"
                  channels: "Email, Push"
                  status: "sent"
                  created_at: "2025-11-11 14:30:00"
  
  /api/stats:
    get:
      summary: Statistiques (API)
      description: |
        Retourne les statistiques complètes du système.
        
        **Métriques:**
        - Nombre total de notifications
        - Nombre total d'utilisateurs
        - Répartition par type d'urgence
        - Répartition par priorité
        - 10 dernières notifications
      tags:
        - API
        - Statistiques
      responses:
        '200':
          description: Statistiques du système
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Statistics'
              example:
                total_notifications: 156
                total_users: 12
                by_type:
                  académique: 120
                  météo: 15
                  sécurité: 10
                  santé: 8
                  infrastructure: 3
                by_priority:
                  LOW: 120
                  MEDIUM: 15
                  HIGH: 10
                  CRITICAL: 11
                recent_notifications:
                  - id: 156
                    title: "Dernière notification"
                    created_at: "2025-11-11 16:45:00"

components:
  schemas:
    User:
      type: object
      required:
        - name
        - email
      properties:
        id:
          type: integer
          description: ID unique de l'utilisateur
          example: 1
        name:
          type: string
          description: Nom complet
          example: "Alice Martin"
        email:
          type: string
          format: email
          description: Adresse email (validée)
          example: "alice.martin@universite.edu"
        phone:
          type: string
          pattern: '^\+?[1-9]\d{1,14}$'
          description: Numéro de téléphone international (optionnel)
          example: "+33612345678"
          nullable: true
        prefers_email:
          type: boolean
          description: Préfère recevoir les notifications par email
          default: true
        created_at:
          type: string
          format: date-time
          description: Date de création
          example: "2025-11-10T10:30:00Z"
    
    Notification:
      type: object
      required:
        - user_id
        - title
        - body
        - emergency_type
        - priority
      properties:
        id:
          type: integer
          description: ID unique de la notification
          example: 1
        user_id:
          type: integer
          description: ID de l'utilisateur destinataire
          example: 1
        user_name:
          type: string
          description: Nom de l'utilisateur destinataire
          example: "Alice Martin"
        title:
          type: string
          maxLength: 200
          description: Titre de la notification
          example: "Alerte Météo"
        body:
          type: string
          description: Corps du message
          example: "Tempête prévue cet après-midi"
        emergency_type:
          type: string
          enum:
            - météo
            - sécurité
            - santé
            - infrastructure
            - académique
          description: Type d'urgence
          example: "météo"
        priority:
          type: string
          enum:
            - LOW
            - MEDIUM
            - HIGH
            - CRITICAL
          description: Niveau de priorité (déterminé automatiquement)
          example: "HIGH"
        channels:
          type: string
          description: Canaux utilisés pour l'envoi (CSV)
          example: "Email, SMS, Push"
          nullable: true
        status:
          type: string
          enum:
            - sent
            - failed
            - pending
          description: Statut de l'envoi
          default: sent
          example: "sent"
        created_at:
          type: string
          format: date-time
          description: Date d'envoi
          example: "2025-11-11T14:30:00Z"
    
    PerformanceMetric:
      type: object
      properties:
        id:
          type: integer
          description: ID unique de la métrique
          example: 1
        method_name:
          type: string
          description: Nom de la méthode mesurée
          example: "send_email"
        duration:
          type: number
          format: float
          description: Durée d'exécution en secondes
          example: 0.234
        timestamp:
          type: string
          format: date-time
          description: Horodatage de la mesure
          example: "2025-11-11T14:30:15Z"
    
    Statistics:
      type: object
      properties:
        total_notifications:
          type: integer
          description: Nombre total de notifications envoyées
          example: 156
        total_users:
          type: integer
          description: Nombre total d'utilisateurs
          example: 12
        by_type:
          type: object
          description: Répartition par type d'urgence
          additionalProperties:
            type: integer
          example:
            académique: 120
            météo: 15
            sécurité: 10
        by_priority:
          type: object
          description: Répartition par priorité
          additionalProperties:
            type: integer
          example:
            LOW: 120
            MEDIUM: 15
            HIGH: 10
            CRITICAL: 11
        recent_notifications:
          type: array
          description: 10 dernières notifications
          items:
            $ref: '#/components/schemas/Notification'
    
    EmergencyType:
      type: string
      enum:
        - météo
        - sécurité
        - santé
        - infrastructure
        - académique
      description: |
        Type d'urgence qui détermine la priorité:
        - **sécurité, santé** → CRITICAL (tous les canaux)
        - **météo** → HIGH
        - **infrastructure** → MEDIUM
        - **académique** → LOW
    
    Priority:
      type: string
      enum:
        - LOW
        - MEDIUM
        - HIGH
        - CRITICAL
      description: |
        Niveau de priorité (déterminé automatiquement):
        - **CRITICAL** (4): Email + SMS + Push
        - **HIGH** (3): Email ou Push (selon préférence)
        - **MEDIUM** (2): Email ou Push (selon préférence)
        - **LOW** (1): Email ou Push (selon préférence)
    
    Error:
      type: object
      properties:
        error:
          type: string
          description: Message d'erreur
          example: "Tous les champs sont requis"
        field:
          type: string
          description: Champ en erreur (si applicable)
          example: "email"
          nullable: true

  securitySchemes:
    SessionAuth:
      type: apiKey
      in: cookie
      name: session
      description: |
        Authentification par session Flask.
        
        **Note:** Actuellement, l'API ne nécessite pas d'authentification.
        En production, il faudrait ajouter:
        - Flask-Login pour authentification
        - JWT tokens pour API
        - CORS pour accès cross-origin

security: []

```

## Guide d'Utilisation de l'API

### 1. Envoi d'une Notification

**Exemple cURL:**
```bash
curl -X POST http://localhost:5000/send-notification \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=1" \
  -d "title=Alerte Académique" \
  -d "body=Rappel: Examen demain à 9h" \
  -d "emergency_type=académique"
```

**Exemple Python:**
```python
import requests

url = "http://localhost:5000/send-notification"
data = {
    "user_id": 1,
    "title": "Alerte Académique",
    "body": "Rappel: Examen demain à 9h",
    "emergency_type": "académique"
}

response = requests.post(url, data=data, allow_redirects=True)
print(response.status_code)
```

**Exemple JavaScript:**
```javascript
const formData = new FormData();
formData.append('user_id', '1');
formData.append('title', 'Alerte Académique');
formData.append('body', 'Rappel: Examen demain à 9h');
formData.append('emergency_type', 'académique');

fetch('http://localhost:5000/send-notification', {
    method: 'POST',
    body: formData
})
.then(response => response.text())
.then(html => console.log('Success'));
```

### 2. Récupération des Notifications (API JSON)

**Exemple cURL:**
```bash
curl -X GET http://localhost:5000/api/notifications \
  -H "Accept: application/json"
```

**Exemple Python:**
```python
import requests

url = "http://localhost:5000/api/notifications"
response = requests.get(url)
notifications = response.json()

for notif in notifications:
    print(f"{notif['title']} - {notif['priority']}")
```

**Exemple JavaScript:**
```javascript
fetch('http://localhost:5000/api/notifications')
    .then(response => response.json())
    .then(notifications => {
        notifications.forEach(notif => {
            console.log(`${notif.title} - ${notif.priority}`);
        });
    });
```

### 3. Récupération des Statistiques

**Exemple cURL:**
```bash
curl -X GET http://localhost:5000/api/stats \
  -H "Accept: application/json"
```

**Exemple Python:**
```python
import requests

url = "http://localhost:5000/api/stats"
response = requests.get(url)
stats = response.json()

print(f"Total notifications: {stats['total_notifications']}")
print(f"Total users: {stats['total_users']}")
print(f"By type: {stats['by_type']}")
```

### 4. Ajout d'un Utilisateur

**Exemple cURL:**
```bash
curl -X POST http://localhost:5000/admin/add-user \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Bob Dupont" \
  -d "email=bob@example.com" \
  -d "phone=+33612345678" \
  -d "prefers_email=on"
```

**Exemple Python:**
```python
import requests

url = "http://localhost:5000/admin/add-user"
data = {
    "name": "Bob Dupont",
    "email": "bob@example.com",
    "phone": "+33612345678",
    "prefers_email": "on"
}

response = requests.post(url, data=data, allow_redirects=True)
```

## Codes de Statut HTTP

| Code | Description | Cas d'Usage |
|------|-------------|-------------|
| **200** | OK | Page chargée avec succès |
| **302** | Found (Redirect) | Redirection après POST |
| **400** | Bad Request | Données invalides |
| **404** | Not Found | Ressource introuvable |
| **500** | Internal Server Error | Erreur serveur |

## Gestion des Erreurs

### Validation des Données

**Email Invalide:**
```json
{
  "error": "Email invalide : invalid-email",
  "field": "email"
}
```

**Téléphone Invalide:**
```json
{
  "error": "Numéro de téléphone invalide : 123",
  "field": "phone"
}
```

**Champs Manquants:**
```json
{
  "error": "Tous les champs sont requis"
}
```

### Circuit Breaker

Lorsque le circuit est ouvert (trop d'échecs récents):

```json
{
  "error": "Circuit ouvert : trop d'échecs récents"
}
```

**Récupération:**
- Timeout: 60 secondes
- Après le timeout, le circuit se ferme automatiquement
- Premier envoi réussi réinitialise le compteur

## Limites et Quotas

| Ressource | Limite | Notes |
|-----------|--------|-------|
| **Requêtes/seconde** | Illimité (dev) | En production: à définir |
| **Taille du titre** | 200 caractères | Validation côté serveur |
| **Taille du body** | Illimité (TEXT) | Recommandé: < 5000 caractères |
| **Utilisateurs** | Illimité | SQLite: ~100K, PostgreSQL: illimité |
| **Notifications/requête** | 1 | Envoi séquentiel |
| **Canaux/notification** | 3 max | Email, SMS, Push |

## Performance

### Métriques Actuelles

| Endpoint | Temps de Réponse | Throughput |
|----------|------------------|------------|
| **/send-notification** | ~300ms | 4 req/s |
| **/api/notifications** | ~5ms | 200 req/s |
| **/api/stats** | ~10ms | 100 req/s |
| **/dashboard** | ~15ms | 60 req/s |

### Optimisations Recommandées

1. **Caching Redis:**
   ```python
   @cache.cached(timeout=60)
   @app.route('/api/stats')
   def api_stats():
       ...
   ```

2. **Queue Asynchrone (Celery):**
   ```python
   @celery.task
   def send_notification_async(...):
       ...
   ```

3. **Database Pooling:**
   ```python
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'pool_size': 10,
       'pool_recycle': 3600
   }
   ```

## Sécurité

### Recommandations pour Production

1. **Authentification:**
   - Ajouter Flask-Login
   - Tokens JWT pour API
   - Rate limiting par IP

2. **CORS:**
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": "https://app.example.com"}})
   ```

3. **HTTPS:**
   - Certificat SSL/TLS
   - Redirect HTTP → HTTPS
   - HSTS headers

4. **Validation:**
   - CSRF protection (déjà activé)
   - Input sanitization
   - SQL injection prevention (ORM)

5. **Secrets:**
   - Variables d'environnement
   - Pas de secrets en clair
   - Rotation régulière

## Webhooks (Future Feature)

### Configuration Webhook

```json
POST /api/webhooks/subscribe
{
  "url": "https://your-app.com/webhook",
  "events": ["notification.sent", "notification.failed"],
  "secret": "your-webhook-secret"
}
```

### Payload Webhook

```json
{
  "event": "notification.sent",
  "timestamp": "2025-11-11T14:30:00Z",
  "data": {
    "notification_id": 123,
    "user_id": 1,
    "title": "Alerte",
    "channels": ["email", "push"],
    "priority": "HIGH"
  }
}
```

## Support et Contact

- **Documentation**: https://docs.academic-notifications.edu
- **Support**: support@academic-notifications.edu
- **GitHub**: https://github.com/academic-notifications/api
- **Status Page**: https://status.academic-notifications.edu
