"""
Système de notification avec mixins et héritage multiple
"""
import random
import time
from enum import Enum
import logging
from core.metaclasses import ChannelMeta, NotificationMeta
from core.decorators import (
    add_performance_tracking,
    auto_configuration_validation,
    register_in_global_registry,
    add_circuit_breaker
)
from models import db, Notification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class EmergencyType(Enum):
    WEATHER = "météo"
    SECURITY = "sécurité"
    HEALTH = "santé"
    INFRASTRUCTURE = "infrastructure"
    ACADEMIC = "académique"


class Priority(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


def get_priority(emergency_type):
    """Détermine la priorité basée sur le type d'urgence"""
    if emergency_type in [EmergencyType.SECURITY, EmergencyType.HEALTH]:
        return Priority.CRITICAL
    elif emergency_type == EmergencyType.WEATHER:
        return Priority.HIGH
    elif emergency_type == EmergencyType.INFRASTRUCTURE:
        return Priority.MEDIUM
    else:
        return Priority.LOW


def log_notification(func):
    """Décorateur de fonction pour logger les notifications"""
    def wrapper(*args, **kwargs):
        print(f"[LOG] Début : {func.__name__}")
        result = func(*args, **kwargs)
        print(f"[LOG] Fin : {func.__name__}")
        return result
    return wrapper


def retry_on_failure(retries=3):
    """Décorateur pour réessayer en cas d'échec"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[ERREUR] Tentative {attempt}/{retries}: {e}")
                    if attempt == retries:
                        raise
            return None
        return wrapper
    return decorator


class SMSMixin:
    """Mixin pour l'envoi de SMS"""
    channel_type = 'sms'
    
    @log_notification
    @retry_on_failure(retries=3)
    def send_sms(self, message, number):
        start_time = time.time()
        
        if random.random() < 0.1:
            raise Exception("Échec d'envoi SMS")
        
        result = {
            'status': 'success',
            'channel': 'SMS',
            'recipient': number,
            'message': message
        }
        
        if hasattr(self, '_track_performance'):
            self._track_performance(time.time() - start_time, 'send_sms')
        
        return result


class EmailMixin:
    """Mixin pour l'envoi d'emails"""
    channel_type = 'email'
    
    @log_notification
    @retry_on_failure(retries=3)
    def send_email(self, message, email):
        start_time = time.time()
        
        if random.random() < 0.1:
            raise Exception("Échec d'envoi Email")
        
        result = {
            'status': 'success',
            'channel': 'Email',
            'recipient': email,
            'message': message
        }
        
        if hasattr(self, '_track_performance'):
            self._track_performance(time.time() - start_time, 'send_email')
        
        return result


class PushNotificationMixin:
    """Mixin pour l'envoi de notifications push"""
    channel_type = 'push'
    
    @log_notification
    @retry_on_failure(retries=3)
    def send_push(self, message, user_id):
        start_time = time.time()
        
        if random.random() < 0.1:
            raise Exception("Échec d'envoi Notification Push")
        
        result = {
            'status': 'success',
            'channel': 'Push',
            'recipient': user_id,
            'message': message
        }
        
        if hasattr(self, '_track_performance'):
            self._track_performance(time.time() - start_time, 'send_push')
        
        return result


class FormattingMixin:
    """Mixin pour le formatage des messages"""
    
    def format_message(self, title, body, emergency_type=None):
        formatted = f"{title}\n{body}"
        if emergency_type:
            formatted = f"[{emergency_type.value.upper()}] {formatted}"
        return formatted


class ArchiveMixin:
    """Mixin pour l'archivage des notifications"""
    
    def archive_notification(self, notification_data):
        """Sauvegarde la notification dans la base de données"""
        from flask import current_app
        
        with current_app.app_context():
            logging.info(f"Attempting to archive notification: {notification_data['title']}")
            try:
                # Créer une nouvelle notification dans la base de données
                notification = Notification(
                    user_id=notification_data['user_id'],
                    title=notification_data['title'],
                    body=notification_data['body'],
                    emergency_type=notification_data['emergency_type'],
                    priority=notification_data['priority'],
                    channels=','.join([r['channel'] for r in notification_data.get('results', []) if r.get('status') == 'success'])
                )
                
                db.session.add(notification)
                db.session.commit()
                
                # Ajouter l'ID de la notification aux données retournées
                notification_data['notification_id'] = notification.id
                logging.info(f"Notification {notification.id} archived successfully.")
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error archiving notification {notification_data['title']}: {e}", exc_info=True)
                raise # Re-raise the exception to be caught by the worker
        return notification_data


class UserPreferenceMixin:
    """Mixin pour gérer les préférences utilisateur"""
    
    def prefers_email(self, user):
        return user.get('prefers_email', True)


@add_performance_tracking
@auto_configuration_validation
@register_in_global_registry
@add_circuit_breaker(max_failures=5, timeout=60)
class AcademicNotifier(SMSMixin, EmailMixin, PushNotificationMixin, 
                       FormattingMixin, ArchiveMixin, UserPreferenceMixin,
                       metaclass=NotificationMeta):
    """Notificateur académique avec tous les concepts POO avancés"""
    
    required_fields = []
    description = "Système de notification académique complet"
    
    def __init__(self):
        self._notification_type = 'academic'
    
    def send_all_channels(self, message, user):
        """Envoie la notification sur tous les canaux disponibles"""
        results = []
        
        try:
            results.append(self.send_email(message, user['email']))
        except Exception as e:
            print(f"Erreur Email: {e}")
        
        try:
            results.append(self.send_push(message, user['id']))
        except Exception as e:
            print(f"Erreur Push: {e}")
        
        if 'phone' in user and user['phone']:
            try:
                results.append(self.send_sms(message, user['phone']))
            except Exception as e:
                print(f"Erreur SMS: {e}")
        
        return results
    
    def notify(self, user, title, body, emergency_type=EmergencyType.ACADEMIC):
        """Envoie une notification selon le type d'urgence et les préférences"""
        
        if self.is_circuit_open():
            raise Exception("Circuit ouvert : trop d'échecs récents")
        
        try:
            priority = get_priority(emergency_type)
            message = self.format_message(title, body, emergency_type)
            
            results = []
            
            if priority == Priority.CRITICAL:
                results = self.send_all_channels(message, user)
            else:
                if self.prefers_email(user):
                    results.append(self.send_email(message, user['email']))
                else:
                    results.append(self.send_push(message, user['id']))
            
            notification_data = {
                'user_id': user['id'],
                'title': title,
                'body': body,
                'emergency_type': emergency_type.value,
                'priority': priority.name,
                'results': results
            }
            
            self.archive_notification(notification_data)
            self.record_success()
            
            return notification_data
            
        except Exception as e:
            self.record_failure()
            raise
