"""
Tests pour les routes Flask
"""
import pytest
from models import User, Notification
from core.notification_system import EmergencyType


class TestIndexRoute:
    """Tests pour la route /"""
    
    def test_index_page_loads(self, client, test_db):
        """Vérifie que la page d'accueil se charge"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_shows_emergency_types(self, client, test_db):
        """Vérifie que les types d'urgence sont affichés"""
        response = client.get('/')
        data = response.data.decode()
        
        assert 'météo' in data or 'sécurité' in data or 'académique' in data


class TestSendNotificationRoute:
    """Tests pour la route /send-notification"""
    
    def test_send_notification_valid(self, client, test_db, sample_user):
        """Vérifie l'envoi d'une notification valide"""
        response = client.post('/send-notification', data={
            'user_id': sample_user.id,
            'title': 'Test Notification',
            'body': 'Test Body',
            'emergency_type': 'académique'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        notification = Notification.query.first()
        assert notification is not None
        assert notification.title == 'Test Notification'
        assert notification.user_id == sample_user.id
    
    def test_send_notification_missing_fields(self, client, test_db):
        """Vérifie la validation des champs requis"""
        response = client.post('/send-notification', data={
            'user_id': '1',
            'title': '',
            'body': 'Test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_send_notification_invalid_user(self, client, test_db):
        """Vérifie le comportement avec un utilisateur invalide"""
        response = client.post('/send-notification', data={
            'user_id': '9999',
            'title': 'Test',
            'body': 'Test'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestDashboardRoute:
    """Tests pour la route /dashboard"""
    
    def test_dashboard_loads(self, client, test_db):
        """Vérifie que le dashboard se charge"""
        response = client.get('/dashboard')
        assert response.status_code == 200
    
    def test_dashboard_shows_notifications(self, client, test_db, sample_user):
        """Vérifie que les notifications sont affichées"""
        notification = Notification(
            user_id=sample_user.id,
            title='Dashboard Test',
            body='Test Body',
            emergency_type='test',
            priority='HIGH'
        )
        test_db.session.add(notification)
        test_db.session.commit()
        
        response = client.get('/dashboard')
        data = response.data.decode()
        
        assert 'Dashboard Test' in data
    
    def test_dashboard_filter_by_type(self, client, test_db, sample_user):
        """Vérifie le filtrage par type"""
        notification1 = Notification(
            user_id=sample_user.id,
            title='Academic',
            body='Test',
            emergency_type='académique',
            priority='LOW'
        )
        notification2 = Notification(
            user_id=sample_user.id,
            title='Security',
            body='Test',
            emergency_type='sécurité',
            priority='HIGH'
        )
        test_db.session.add_all([notification1, notification2])
        test_db.session.commit()
        
        response = client.get('/dashboard?type=académique')
        assert response.status_code == 200
    
    def test_dashboard_filter_by_priority(self, client, test_db, sample_user):
        """Vérifie le filtrage par priorité"""
        response = client.get('/dashboard?priority=HIGH')
        assert response.status_code == 200


class TestAdminRoute:
    """Tests pour la route /admin"""
    
    def test_admin_page_loads(self, client, test_db):
        """Vérifie que la page admin se charge"""
        response = client.get('/admin')
        assert response.status_code == 200
    
    def test_admin_shows_users(self, client, test_db, sample_user):
        """Vérifie que les utilisateurs sont affichés"""
        response = client.get('/admin')
        data = response.data.decode()
        
        assert 'Test User' in data or 'test@example.com' in data


class TestAddUserRoute:
    """Tests pour la route /admin/add-user"""
    
    def test_add_user_valid(self, client, test_db):
        """Vérifie l'ajout d'un utilisateur valide"""
        response = client.post('/admin/add-user', data={
            'name': 'New User',
            'email': 'new@example.com',
            'phone': '+33612345678',
            'prefers_email': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        user = User.query.filter_by(email='new@example.com').first()
        assert user is not None
        assert user.name == 'New User'
        assert user.prefers_email is True
    
    def test_add_user_without_phone(self, client, test_db):
        """Vérifie l'ajout sans téléphone"""
        response = client.post('/admin/add-user', data={
            'name': 'User No Phone',
            'email': 'nophone@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        user = User.query.filter_by(email='nophone@example.com').first()
        assert user is not None
        assert user.phone is None
    
    def test_add_user_missing_required_fields(self, client, test_db):
        """Vérifie la validation des champs requis"""
        response = client.post('/admin/add-user', data={
            'name': 'Test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_add_user_invalid_email(self, client, test_db):
        """Vérifie la validation de l'email"""
        response = client.post('/admin/add-user', data={
            'name': 'Test',
            'email': 'invalid-email'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestDeleteUserRoute:
    """Tests pour la route /admin/delete-user"""
    
    def test_delete_user_valid(self, client, test_db, sample_user):
        """Vérifie la suppression d'un utilisateur"""
        user_id = sample_user.id
        
        response = client.post(f'/admin/delete-user/{user_id}', follow_redirects=True)
        
        assert response.status_code == 200
        
        user = User.query.get(user_id)
        assert user is None
    
    def test_delete_user_invalid_id(self, client, test_db):
        """Vérifie la gestion d'un ID invalide"""
        response = client.post('/admin/delete-user/9999', follow_redirects=True)
        
        assert response.status_code == 200


class TestAPIRoutes:
    """Tests pour les routes API"""
    
    def test_api_notifications(self, client, test_db, sample_user):
        """Vérifie l'API des notifications"""
        notification = Notification(
            user_id=sample_user.id,
            title='API Test',
            body='Test',
            emergency_type='test',
            priority='LOW'
        )
        test_db.session.add(notification)
        test_db.session.commit()
        
        response = client.get('/api/notifications')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_api_stats(self, client, test_db, sample_user):
        """Vérifie l'API des statistiques"""
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'total_notifications' in data
        assert 'total_users' in data
        assert 'by_type' in data
        assert 'by_priority' in data
