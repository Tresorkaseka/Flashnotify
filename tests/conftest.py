"""
Configuration et fixtures pytest pour les tests
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Notification, PerformanceMetric


@pytest.fixture
def test_app():
    """Fixture pour l'application Flask de test"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    """Fixture pour le client de test Flask"""
    return test_app.test_client()


@pytest.fixture
def test_db(test_app):
    """Fixture pour la base de données de test"""
    with test_app.app_context():
        yield db


@pytest.fixture
def sample_user(test_db):
    """Fixture pour un utilisateur de test"""
    user = User(
        name='Test User',
        email='test@example.com',
        phone='+33612345678',
        prefers_email=True
    )
    test_db.session.add(user)
    test_db.session.commit()
    return user


@pytest.fixture
def multiple_users(test_db):
    """Fixture pour plusieurs utilisateurs de test"""
    users = [
        User(name='Alice', email='alice@example.com', phone='+33611111111', prefers_email=True),
        User(name='Bob', email='bob@example.com', phone='+33622222222', prefers_email=False),
        User(name='Charlie', email='charlie@example.com', prefers_email=True),
    ]
    for user in users:
        test_db.session.add(user)
    test_db.session.commit()
    return users
