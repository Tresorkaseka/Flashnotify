"""
Tests unitaires pour les modèles de base de données
"""
import pytest
from models import User, Notification, PerformanceMetric, validate_email, validate_phone, validate_priority
from datetime import datetime


class TestValidationFunctions:
    """Tests pour les fonctions de validation"""
    
    def test_validate_email_valid(self):
        """Vérifie la validation d'email valide"""
        email = validate_email('test@example.com')
        assert email == 'test@example.com'
    
    def test_validate_email_invalid(self):
        """Vérifie la détection d'email invalide"""
        with pytest.raises(ValueError):
            validate_email('invalid-email')
    
    def test_validate_phone_valid(self):
        """Vérifie la validation de téléphone valide"""
        phone = validate_phone('+33612345678')
        assert phone == '+33612345678'
    
    def test_validate_phone_invalid(self):
        """Vérifie la détection de téléphone invalide"""
        with pytest.raises(ValueError):
            validate_phone('123')
    
    def test_validate_phone_none(self):
        """Vérifie que None est accepté pour téléphone"""
        phone = validate_phone(None)
        assert phone is None
    
    def test_validate_priority_valid(self):
        """Vérifie la validation de priorité valide"""
        priority = validate_priority('HIGH')
        assert priority == 'HIGH'
    
    def test_validate_priority_normalized(self):
        """Vérifie la normalisation de la priorité"""
        priority = validate_priority('low')
        assert priority == 'LOW'
    
    def test_validate_priority_invalid(self):
        """Vérifie la détection de priorité invalide"""
        with pytest.raises(ValueError):
            validate_priority('INVALID')


class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_create_user_valid(self, test_db):
        """Vérifie la création d'un utilisateur valide"""
        user = User(
            name='Test User',
            email='test@example.com',
            phone='+33612345678',
            prefers_email=True
        )
        
        assert user.name == 'Test User'
        assert user.email == 'test@example.com'
        assert user.phone == '+33612345678'
        assert user.prefers_email is True
    
    def test_create_user_without_phone(self, test_db):
        """Vérifie la création sans numéro de téléphone"""
        user = User(
            name='Test User',
            email='test@example.com'
        )
        
        assert user.phone is None
    
    def test_create_user_invalid_email(self, test_db):
        """Vérifie qu'un email invalide lève une exception"""
        with pytest.raises(ValueError):
            User(
                name='Test User',
                email='invalid-email'
            )
    
    def test_create_user_invalid_phone(self, test_db):
        """Vérifie qu'un téléphone invalide lève une exception"""
        with pytest.raises(ValueError):
            User(
                name='Test User',
                email='test@example.com',
                phone='123'
            )
    
    def test_email_setter_validates(self, test_db):
        """Vérifie que le setter valide l'email"""
        user = User(name='Test', email='test@example.com')
        
        user.email = 'new@example.com'
        assert user.email == 'new@example.com'
        
        with pytest.raises(ValueError):
            user.email = 'invalid-email'
    
    def test_phone_setter_validates(self, test_db):
        """Vérifie que le setter valide le téléphone"""
        user = User(name='Test', email='test@example.com', phone='+33612345678')
        
        user.phone = '+33687654321'
        assert user.phone == '+33687654321'
        
        with pytest.raises(ValueError):
            user.phone = 'invalid'
    
    def test_to_dict_method(self, test_db):
        """Vérifie la méthode to_dict"""
        user = User(
            name='Test User',
            email='test@example.com',
            phone='+33612345678',
            prefers_email=True
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['name'] == 'Test User'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['phone'] == '+33612345678'
        assert user_dict['prefers_email'] is True
        assert 'id' in user_dict
    
    def test_user_repr(self, test_db):
        """Vérifie la représentation string"""
        user = User(name='Test', email='test@example.com')
        assert 'Test' in repr(user)


class TestNotificationModel:
    """Tests pour le modèle Notification"""
    
    def test_create_notification(self, test_db, sample_user):
        """Vérifie la création d'une notification"""
        notification = Notification(
            user_id=sample_user.id,
            title='Test Title',
            body='Test Body',
            emergency_type='académique',
            priority='HIGH',
            channels='Email, Push',
            status='sent'
        )
        
        assert notification.title == 'Test Title'
        assert notification.body == 'Test Body'
        assert notification.emergency_type == 'académique'
        assert notification.priority == 'HIGH'
        assert notification.channels == 'Email, Push'
        assert notification.status == 'sent'
    
    def test_notification_priority_validation(self, test_db, sample_user):
        """Vérifie la validation de la priorité"""
        notification = Notification(
            user_id=sample_user.id,
            title='Test',
            body='Test',
            emergency_type='test',
            priority='low'
        )
        
        assert notification.priority == 'LOW'
    
    def test_notification_invalid_priority(self, test_db, sample_user):
        """Vérifie qu'une priorité invalide lève une exception"""
        with pytest.raises(ValueError):
            Notification(
                user_id=sample_user.id,
                title='Test',
                body='Test',
                emergency_type='test',
                priority='INVALID'
            )
    
    def test_notification_to_dict(self, test_db, sample_user):
        """Vérifie la méthode to_dict"""
        notification = Notification(
            user_id=sample_user.id,
            title='Test',
            body='Body',
            emergency_type='test',
            priority='HIGH',
            channels='Email'
        )
        test_db.session.add(notification)
        test_db.session.commit()
        
        notif_dict = notification.to_dict()
        
        assert notif_dict['title'] == 'Test'
        assert notif_dict['body'] == 'Body'
        assert notif_dict['priority'] == 'HIGH'
        assert notif_dict['user_name'] == 'Test User'
    
    def test_notification_relationship_with_user(self, test_db, sample_user):
        """Vérifie la relation avec User"""
        notification = Notification(
            user_id=sample_user.id,
            title='Test',
            body='Body',
            emergency_type='test',
            priority='MEDIUM'
        )
        test_db.session.add(notification)
        test_db.session.commit()
        
        assert notification.user == sample_user
        assert notification in sample_user.notifications


class TestPerformanceMetricModel:
    """Tests pour le modèle PerformanceMetric"""
    
    def test_create_performance_metric(self, test_db):
        """Vérifie la création d'une métrique"""
        metric = PerformanceMetric(
            method_name='send_email',
            duration=0.234
        )
        test_db.session.add(metric)
        test_db.session.commit()
        
        assert metric.method_name == 'send_email'
        assert metric.duration == 0.234
        assert isinstance(metric.timestamp, datetime)
    
    def test_performance_metric_to_dict(self, test_db):
        """Vérifie la méthode to_dict"""
        metric = PerformanceMetric(
            method_name='send_sms',
            duration=0.156
        )
        test_db.session.add(metric)
        test_db.session.commit()
        
        metric_dict = metric.to_dict()
        
        assert metric_dict['method_name'] == 'send_sms'
        assert metric_dict['duration'] == 0.156
        assert 'timestamp' in metric_dict


class TestDatabaseRelationships:
    """Tests pour les relations entre modèles"""
    
    def test_cascade_delete_user_notifications(self, test_db, sample_user):
        """Vérifie la suppression en cascade des notifications"""
        notification1 = Notification(
            user_id=sample_user.id,
            title='Test 1',
            body='Body 1',
            emergency_type='test',
            priority='LOW'
        )
        notification2 = Notification(
            user_id=sample_user.id,
            title='Test 2',
            body='Body 2',
            emergency_type='test',
            priority='MEDIUM'
        )
        
        test_db.session.add_all([notification1, notification2])
        test_db.session.commit()
        
        assert len(sample_user.notifications) == 2
        
        test_db.session.delete(sample_user)
        test_db.session.commit()
        
        assert Notification.query.count() == 0
