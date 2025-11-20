"""
Système d'authentification et d'autorisation
"""
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import db, User


class Role:
    """Définition des rôles système"""
    ADMIN = "admin"
    USER = "user"
    API_USER = "api_user"
    
    @classmethod
    def get_all_roles(cls):
        return [cls.ADMIN, cls.USER, cls.API_USER]


class Permission:
    """Définition des permissions système"""
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    READ_NOTIFICATIONS = "read_notifications"
    SEND_NOTIFICATIONS = "send_notifications"
    READ_STATS = "read_stats"
    MANAGE_SYSTEM = "manage_system"
    
    @classmethod
    def get_all_permissions(cls):
        return [
            cls.READ_USERS, cls.WRITE_USERS, cls.READ_NOTIFICATIONS,
            cls.SEND_NOTIFICATIONS, cls.READ_STATS, cls.MANAGE_SYSTEM
        ]


class RoleManager:
    """Gestion des rôles et permissions"""
    
    # Définition des permissions par rôle
    ROLE_PERMISSIONS = {
        Role.ADMIN: Permission.get_all_permissions(),
        Role.USER: [Permission.READ_NOTIFICATIONS, Permission.SEND_NOTIFICATIONS],
        Role.API_USER: [Permission.READ_USERS, Permission.READ_NOTIFICATIONS, Permission.SEND_NOTIFICATIONS, Permission.READ_STATS]
    }
    
    @classmethod
    def get_permissions_for_role(cls, role):
        """Retourne les permissions pour un rôle donné"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def has_permission(cls, role, permission):
        """Vérifie si un rôle a une permission donnée"""
        return permission in cls.get_permissions_for_role(role)


class UserSession:
    """Gestion des sessions utilisateurs"""
    
    def __init__(self):
        self.sessions = {}  # token -> session_data
    
    def create_session(self, user_id, role=Role.USER):
        """Crée une nouvelle session pour un utilisateur"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=8)
        
        session_data = {
            'user_id': user_id,
            'role': role,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'token': token
        }
        
        self.sessions[token] = session_data
        return token, expires_at
    
    def validate_session(self, token):
        """Valide une session et retourne les données utilisateur"""
        if token not in self.sessions:
            return None
        
        session_data = self.sessions[token]
        
        if datetime.now() > session_data['expires_at']:
            self.destroy_session(token)
            return None
        
        return session_data
    
    def destroy_session(self, token):
        """Détruit une session"""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False
    
    def refresh_session(self, token):
        """Rafraîchit une session"""
        session_data = self.validate_session(token)
        if not session_data:
            return None
        
        new_expires_at = datetime.now() + timedelta(hours=8)
        session_data['expires_at'] = new_expires_at
        session_data['last_refresh'] = datetime.now()
        
        return session_data['token'], new_expires_at


class AuthManager:
    """Gestionnaire d'authentification principal"""
    
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or 'dev-secret'  # Default to a fixed value to avoid app context issue
        self.session_manager = UserSession()
        self.api_keys = {}  # user_id -> api_key
    
    def hash_password(self, password):
        """Hache un mot de passe avec SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed_password):
        """Vérifie un mot de passe contre son hash"""
        print(f"Vérification du mot de passe - Entrée: {password[:3]}..., Hash stocké: {hashed_password[:10]}... si disponible")
        hashed_input = self.hash_password(password)
        print(f"Hash du mot de passe saisi: {hashed_input[:10]}...")
        result = hashed_input == hashed_password
        print(f"Résultat de la comparaison: {result}")
        return result
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur"""
        try:
            print(f"Recherche d'utilisateur avec email: {email}")
            print(f"Type de l'email: {type(email)}")
            print(f"Longueur de l'email: {len(email) if email else 0}")
            print(f"Email en minuscules: {email.lower()}")
            
            # Essayons d'abord avec filter_by
            user = User.query.filter_by(email=email).first()
            print(f"Résultat de filter_by: {user is not None}")
            
            if not user:
                # Essayons avec une recherche avec LIKE pour voir si c'est un problème de casse ou d'espaces
                user = User.query.filter(User._email.ilike(email)).first()
                print(f"Résultat de filter avec ilike: {user is not None}")
                
                if not user:
                    # Finalement, essayons de récupérer tous les utilisateurs pour voir exactement ce qui est stocké
                    print("Liste complète des emails dans la base :")
                    all_users = User.query.all()
                    for u in all_users:
                        print(f"  - '{u.email}' (longueur: {len(u.email)})")
                        print(f"    Correspondance exacte: '{u.email}' == '{email}' -> {u.email == email}")
                
                if not user:
                    # Essayons avec une recherche exacte de tous les utilisateurs pour déboguer
                    all_users = User.query.all()
                    print(f"Total des utilisateurs dans la base: {len(all_users)}")
                    for u in all_users:
                        print(f" - {repr(u.email)} (id: {u.id})")
                        print(f"    Correspondance exacte: {u.email == email}")
                        print(f"    Correspondance lower: {u.email.lower() == email.lower()}")
            
            if user:
                print(f"Utilisateur trouvé: {user.email}, Role: {user.role}")
                print(f"Mot de passe dans la base (hash): {user._password[:10]}..." if user._password else "Mot de passe vide")
                # Hacher le mot de passe fourni pour comparaison
                input_password_hash = self.hash_password(password)
                print(f"Mot de passe saisi hashé: {input_password_hash[:10]}...")
                
                # Récupérer le mot de passe haché directement via l'attribut _password
                stored_password = user._password
                print(f"Type du mot de passe stocké: {type(stored_password)}")
                print(f"Longueur du mot de passe stocké: {len(stored_password) if stored_password else 0}")
                
                passwords_match = self.verify_password(password, stored_password)
                print(f"Comparaison des mots de passe: {passwords_match}")
                
                if passwords_match:
                    print("Authentification réussie!")
                    return user
                else:
                    print("Échec d'authentification: mots de passe ne correspondent pas")
            else:
                print("Aucun utilisateur trouvé avec cet email")
        except Exception as e:
            import traceback
            print(f"Erreur dans authenticate_user: {str(e)}")
            print(f"Traceback complet: {traceback.format_exc()}")
        return None
    
    def create_user_session(self, user, role=Role.USER):
        """Crée une session pour un utilisateur"""
        return self.session_manager.create_session(user.id, role)
    
    def validate_user_session(self, token):
        """Valide une session utilisateur"""
        return self.session_manager.validate_session(token)
    
    def create_api_key(self, user_id, permissions=None):
        """Crée une clé API pour un utilisateur"""
        api_key = secrets.token_urlsafe(64)
        self.api_keys[user_id] = {
            'key': api_key,
            'permissions': permissions or [Permission.READ_NOTIFICATIONS, Permission.SEND_NOTIFICATIONS],
            'created_at': datetime.now()
        }
        return api_key
    
    def validate_api_key(self, api_key):
        """Valide une clé API"""
        for user_id, data in self.api_keys.items():
            if data['key'] == api_key:
                return {'user_id': user_id, 'permissions': data['permissions']}
        return None
    
    def generate_jwt_token(self, user_id, role=Role.USER, expires_in_hours=24):
        """Génère un token JWT"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.now() + timedelta(hours=expires_in_hours),
            'iat': datetime.now()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token):
        """Vérifie un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


# Instances globales
auth_manager = AuthManager()


def require_auth(f):
    """Décorateur pour les routes nécessitant une authentification"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token d\'authentification requis'}), 401
        
        try:
            token_type, token = auth_header.split(' ', 1)
            
            if token_type.lower() == 'bearer':
                # Validation JWT
                payload = auth_manager.verify_jwt_token(token)
                if not payload:
                    return jsonify({'error': 'Token invalide ou expiré'}), 401
                request.current_user = payload
            
            elif token_type.lower() == 'api-key':
                # Validation API Key
                api_data = auth_manager.validate_api_key(token)
                if not api_data:
                    return jsonify({'error': 'Clé API invalide'}), 401
                request.current_user = api_data
            
            elif token_type.lower() == 'session':
                # Validation session
                session_data = auth_manager.validate_user_session(token)
                if not session_data:
                    return jsonify({'error': 'Session invalide ou expirée'}), 401
                request.current_user = session_data
            
            else:
                return jsonify({'error': 'Type d\'authentification non supporté'}), 401
            
        except ValueError:
            return jsonify({'error': 'En-tête d\'authentification invalide'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def require_permission(permission):
    """Décorateur pour les routes nécessitant une permission spécifique"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            current_user = getattr(request, 'current_user', {})
            user_role = current_user.get('role', Role.USER)
            
            if not RoleManager.has_permission(user_role, permission):
                return jsonify({'error': 'Permission refusée'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def create_default_admin():
    """Crée un utilisateur admin par défaut si aucun admin n'existe"""
    admin_exists = User.query.filter(User.email.endswith('@admin.local')).first()
    if not admin_exists:
        admin_user = User(
            name='Admin User',
            email='admin@flashnotify.local',
            phone=None,
            prefers_email=True
        )
        # Le mot de passe sera haché dans le modèle User
        admin_user._password = auth_manager.hash_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        return admin_user
    return admin_exists