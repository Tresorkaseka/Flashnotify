"""
Script pour réinitialiser la base de données et créer les utilisateurs avec les bons mots de passe
"""
import os
from app import app, db
from models import User
from core.auth import auth_manager

def reset_database():
    with app.app_context():
        # Supprimer toutes les tables
        db.drop_all()
        
        # Recréer toutes les tables
        db.create_all()
        
        # Créer un utilisateur admin
        admin_user = User(
            name='Admin User',
            email='admin@flashnotify.local',
            phone=None,
            password=auth_manager.hash_password('admin123'),  # Mot de passe haché directement
            role='admin',
            prefers_email=True
        )
        db.session.add(admin_user)
        
        # Créer des utilisateurs de test
        users = [
            User(name='Alice Martin', email='alice.martin@universite.edu', phone='+33612345678',
                 password=auth_manager.hash_password('user123'), role='user', prefers_email=True),
            User(name='Bob Dupont', email='bob.dupont@universite.edu', phone='+33623456789',
                 password=auth_manager.hash_password('user123'), role='user', prefers_email=False),
            User(name='Charlie Bernard', email='charlie.bernard@universite.edu',
                 password=auth_manager.hash_password('user123'), role='user', prefers_email=True),
        ]
        
        for user in users:
            db.session.add(user)
        
        db.session.commit()
        
        print("Base de données réinitialisée avec succès")
        print(f"Nombre d'utilisateurs créés: {User.query.count()}")
        
        # Afficher les utilisateurs pour vérification
        all_users = User.query.all()
        for user in all_users:
            print(f"User: {user.email}, Role: {user.role}, Password length: {len(user._password) if user._password else 0}")

if __name__ == "__main__":
    reset_database()