"""
Modèles de base de données avec SQLAlchemy
Utilise la validation par descripteurs
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()


def validate_email(email):
    """Valide le format email (utilise la logique du EmailDescriptor)"""
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError(f"Email invalide : {email}")
    return email


def validate_phone(phone):
    """Valide le format téléphone international (utilise la logique du PhoneDescriptor)"""
    if phone:
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, phone):
            raise ValueError(f"Numéro de téléphone invalide : {phone}")
    return phone


def validate_priority(priority):
    """Valide le niveau de priorité (utilise la logique du PriorityDescriptor)"""
    valid_priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    if priority and priority.upper() not in valid_priorities:
        raise ValueError(f"Priorité invalide : {priority}. Valeurs acceptées : {valid_priorities}")
    return priority.upper() if priority else 'MEDIUM'


class User(db.Model):
    """Modèle utilisateur avec validation automatique"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    _email = db.Column('email', db.String(120), unique=True, nullable=False)
    _phone = db.Column('phone', db.String(20), nullable=True)
    _password = db.Column('password', db.String(255), nullable=False)  # Added password field
    role = db.Column(db.String(20), default='user')  # Added role field
    prefers_email = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, email, phone=None, password=None, role='user', prefers_email=True):
        self.name = name
        self._email = validate_email(email)
        self._phone = validate_phone(phone) if phone else None
        self._password = password  # Will be set after hashing in auth system
        self.role = role
        self.prefers_email = prefers_email
    
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        self._email = validate_email(value)
    
    @property
    def phone(self):
        return self._phone
    
    @phone.setter
    def phone(self, value):
        self._phone = validate_phone(value) if value else None
    
    @property
    def password(self):
        return self._password
    
    @password.setter
    def password(self, value):
        # Password should be hashed before setting
        self._password = value
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self._email,
            'phone': self._phone,
            'prefers_email': self.prefers_email,
            'role': self.role  # Include role in dict
        }
    
    
    def __repr__(self):
        return f'<User {self.name}>'


class Notification(db.Model):
    """Modèle pour l'historique des notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    emergency_type = db.Column(db.String(50), nullable=False)
    _priority = db.Column('priority', db.String(20), nullable=False)
    channels = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='sent')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, title, body, emergency_type, priority, channels=None, status='sent'):
        self.user_id = user_id
        self.title = title
        self.body = body
        self.emergency_type = emergency_type
        self._priority = validate_priority(priority)
        self.channels = channels
        self.status = status
    
    @property
    def priority(self):
        return self._priority
    
    @priority.setter
    def priority(self, value):
        self._priority = validate_priority(value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'title': self.title,
            'body': self.body,
            'emergency_type': self.emergency_type,
            'priority': self._priority,
            'channels': self.channels,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class PerformanceMetric(db.Model):
    """Modèle pour les métriques de performance"""
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    method_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'method_name': self.method_name,
            'duration': round(self.duration, 4),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<PerformanceMetric {self.method_name}: {self.duration}s>'
