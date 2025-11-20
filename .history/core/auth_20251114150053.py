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
        return self.hash_password(password) == hashed_password
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur"""
        user = User.query.filter_by(email=email).first()
        if user:
            # Récupérer le mot de passe haché directement via l'attribut _password
            stored_password = user._password
            if self.verify_password(password, stored_password):
                return user
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