"""
Modèles de base de données avec SQLAlchemy
Utilise les descripteurs pour la validation automatique
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from core.descriptors import EmailDescriptor, PhoneDescriptor, PriorityDescriptor

db = SQLAlchemy()


class User(db.Model):
    """Modèle utilisateur avec descripteurs pour validation"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    _email = db.Column('email', db.String(120), unique=True, nullable=False)
    _phone = db.Column('phone', db.String(20), nullable=True)
    prefers_email = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    email = EmailDescriptor()
    phone = PhoneDescriptor()
    
    def __init__(self, name, email, phone=None, prefers_email=True):
        self.name = name
        self.email = email
        self.phone = phone
        self.prefers_email = prefers_email
    
    @property
    def _email_value(self):
        return self._email
    
    @_email_value.setter
    def _email_value(self, value):
        self._email = value
    
    @property
    def _phone_value(self):
        return self._phone
    
    @_phone_value.setter
    def _phone_value(self, value):
        self._phone = value
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self._email,
            'phone': self._phone,
            'prefers_email': self.prefers_email
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
    
    priority = PriorityDescriptor()
    
    def __init__(self, user_id, title, body, emergency_type, priority, channels=None, status='sent'):
        self.user_id = user_id
        self.title = title
        self.body = body
        self.emergency_type = emergency_type
        self.priority = priority
        self.channels = channels
        self.status = status
    
    @property
    def _priority_value(self):
        return self._priority
    
    @_priority_value.setter
    def _priority_value(self, value):
        self._priority = value
    
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
