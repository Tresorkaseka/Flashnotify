"""
Tests d'intégration du système complet
"""
import pytest
from core.notification_system import AcademicNotifier, EmergencyType, Priority
from core.metaclasses import NotificationRegistry
from models import User, Notification, PerformanceMetric


class TestNotificationSystemIntegration:
    """Tests d'intégration pour le système de notification"""
    
    def test_full_notification_workflow(self, test_db):
        """Test complet du workflow de notification"""
        user = User(
            name='Integration User',
            email='integration@example.com',
            phone='+33612345678',
            prefers_email=True
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        notifier = AcademicNotifier()
        
        result = notifier.notify(
            user.to_dict(),
            "Integration Test",
            "This is an integration test",
            EmergencyType.ACADEMIC
        )
        
        assert result is not None
        assert result['user_id'] == str(user.id)
        assert result['title'] == "Integration Test"
        assert result['priority'] == Priority.LOW.name
        assert len(result['results']) > 0
    
    def test_notifier_with_all_features(self, test_db):
        """Vérifie que toutes les features POA fonctionnent ensemble"""
        notifier = AcademicNotifier()
        
        assert hasattr(notifier, '_notification_type')
        assert notifier._notification_type == 'academic'
        
        assert hasattr(notifier, 'get_performance_metrics')
        
        assert hasattr(notifier, 'is_circuit_open')
        
        assert hasattr(notifier, 'send_email')
        assert hasattr(notifier, 'send_sms')
        assert hasattr(notifier, 'send_push')
    
    def test_metaclass_and_decorators_integration(self):
        """Vérifie l'intégration métaclasse + décorateurs"""
        notifier = AcademicNotifier()
        
        assert NotificationRegistry.get('AcademicNotifier') == AcademicNotifier
        
        metrics = notifier.get_performance_metrics()
        assert isinstance(metrics, list)
        
        assert notifier.is_circuit_open() is False
    
    def test_critical_priority_sends_all_channels(self, test_db):
        """Vérifie que CRITICAL envoie sur tous les canaux"""
        user = User(
            name='Critical User',
            email='critical@example.com',
            phone='+33612345678'
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        notifier = AcademicNotifier()
        
        result = notifier.notify(
            user.to_dict(),
            "Critical Alert",
            "This is critical",
            EmergencyType.SECURITY
        )
        
        assert result['priority'] == Priority.CRITICAL.name
        assert len(result['results']) >= 2
    
    def test_performance_tracking_integration(self, test_db):
        """Vérifie le tracking de performance intégré"""
        user = User(
            name='Perf User',
            email='perf@example.com',
            phone='+33612345678'
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        notifier = AcademicNotifier()
        
        notifier.notify(
            user.to_dict(),
            "Performance Test",
            "Testing performance",
            EmergencyType.ACADEMIC
        )
        
        metrics = notifier.get_performance_metrics()
        
        assert len(metrics) > 0
        assert all('method' in m for m in metrics)
        assert all('duration' in m for m in metrics)
        assert all('timestamp' in m for m in metrics)
    
    def test_circuit_breaker_integration(self):
        """Vérifie l'intégration du circuit breaker"""
        notifier = AcademicNotifier()
        
        assert notifier.is_circuit_open() is False
        
        for _ in range(5):
            notifier.record_failure()
        
        assert notifier.is_circuit_open() is True
        
        notifier.record_success()
        assert notifier.is_circuit_open() is False


class TestFlaskDatabaseIntegration:
    """Tests d'intégration Flask + Database"""
    
    def test_end_to_end_notification_creation(self, client, test_db, sample_user):
        """Test de bout en bout: création de notification via Flask"""
        initial_count = Notification.query.count()
        
        response = client.post('/send-notification', data={
            'user_id': sample_user.id,
            'title': 'E2E Test',
            'body': 'End to end test',
            'emergency_type': 'académique'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        final_count = Notification.query.count()
        assert final_count == initial_count + 1
        
        notification = Notification.query.filter_by(title='E2E Test').first()
        assert notification is not None
        assert notification.user_id == sample_user.id
    
    def test_user_crud_operations(self, client, test_db):
        """Test complet CRUD utilisateur"""
        response = client.post('/admin/add-user', data={
            'name': 'CRUD User',
            'email': 'crud@example.com',
            'phone': '+33612345678',
            'prefers_email': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        user = User.query.filter_by(email='crud@example.com').first()
        assert user is not None
        
        user_id = user.id
        
        response = client.post(f'/admin/delete-user/{user_id}', follow_redirects=True)
        assert response.status_code == 200
        
        user = User.query.get(user_id)
        assert user is None
    
    def test_notification_with_metrics_persistence(self, client, test_db, sample_user):
        """Vérifie la persistence des métriques de performance"""
        initial_metrics_count = PerformanceMetric.query.count()
        
        response = client.post('/send-notification', data={
            'user_id': sample_user.id,
            'title': 'Metrics Test',
            'body': 'Test',
            'emergency_type': 'académique'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        final_metrics_count = PerformanceMetric.query.count()
        assert final_metrics_count > initial_metrics_count


class TestValidationIntegration:
    """Tests d'intégration pour la validation"""
    
    def test_validation_chain(self, test_db):
        """Vérifie la chaîne de validation complète"""
        with pytest.raises(ValueError):
            User(name='Test', email='invalid-email')
        
        user = User(name='Valid', email='valid@example.com')
        test_db.session.add(user)
        test_db.session.commit()
        
        with pytest.raises(ValueError):
            user.email = 'invalid'
        
        user.email = 'new@example.com'
        test_db.session.commit()
        
        assert user.email == 'new@example.com'
    
    def test_descriptors_with_orm(self, test_db):
        """Vérifie l'intégration descripteurs + ORM"""
        user = User(
            name='Descriptor Test',
            email='descriptor@example.com',
            phone='+33612345678'
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        fetched_user = User.query.filter_by(email='descriptor@example.com').first()
        
        assert fetched_user.email == 'descriptor@example.com'
        assert fetched_user.phone == '+33612345678'
        
        with pytest.raises(ValueError):
            fetched_user.email = 'invalid'


class TestErrorHandling:
    """Tests d'intégration pour la gestion des erreurs"""
    
    def test_graceful_error_handling(self, client, test_db):
        """Vérifie la gestion des erreurs gracieuse"""
        response = client.post('/send-notification', data={
            'user_id': '9999',
            'title': 'Test',
            'body': 'Test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_database_rollback_on_error(self, test_db):
        """Vérifie le rollback en cas d'erreur"""
        initial_count = User.query.count()
        
        try:
            user = User(name='Rollback Test', email='invalid-email')
            test_db.session.add(user)
            test_db.session.commit()
        except ValueError:
            test_db.session.rollback()
        
        final_count = User.query.count()
        assert final_count == initial_count
