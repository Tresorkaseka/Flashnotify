"""
Application Flask principale - Système de Notification Académique
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from models import db, User, Notification, PerformanceMetric
from core.notification_system import AcademicNotifier, EmergencyType, Priority, get_priority
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///notifications.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from core.auth import auth_manager, Role, require_auth
from functools import wraps
from core.queue import async_queue, thread_pool_queue, init_queues, shutdown_queues, NotificationTask, TaskStatus
import asyncio

notifier = AcademicNotifier()


def login_required(f):
    """Décorateur pour les routes nécessitant une authentification via session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            flash('Veuillez vous connecter', 'error')
            return redirect(url_for('login'))
        
        session_data = auth_manager.validate_user_session(session_token)
        if not session_data:
            flash('Session expirée, veuillez vous reconnecter', 'error')
            return redirect(url_for('login'))
        
        # Stocke les données de session pour utilisation dans la vue et les templates
        request.current_user = session_data
        g.current_user = session_data
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/')
def index():
    """Page d'accueil avec formulaire d'envoi de notification"""
    users = User.query.all()
    emergency_types = [e.value for e in EmergencyType]
    return render_template('index.html', users=users, emergency_types=emergency_types)


@app.route('/send-notification', methods=['POST'])
def send_notification():
    """Envoie une notification de manière asynchrone via la file d'attente"""
    try:
        user_id = request.form.get('user_id')
        title = request.form.get('title')
        body = request.form.get('body')
        emergency_type_value = request.form.get('emergency_type', 'académique')
        
        if not all([user_id, title, body]):
            flash('Tous les champs sont requis', 'error')
            return redirect(url_for('index'))
        
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur introuvable', 'error')
            return redirect(url_for('index'))
        
        emergency_type = None
        for et in EmergencyType:
            if et.value == emergency_type_value:
                emergency_type = et
                break
        
        if not emergency_type:
            emergency_type = EmergencyType.ACADEMIC
        
        # Ajout de la tâche à la file d'attente asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            task_id = loop.run_until_complete(
                async_queue.send_notification_async(
                    user_id=user.id,
                    title=title,
                    body=body,
                    emergency_type=emergency_type_value
                )
            )
            
            flash(f'Notification ajoutée à la file d\'attente (ID: {task_id[:8]}...)', 'success')
            
        except Exception as e:
            flash(f'Erreur lors de l\'ajout à la file d\'attente: {str(e)}', 'error')
        finally:
            loop.close()
        
    except Exception as e:
        flash(f'Erreur de validation: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard des notifications"""
    filter_type = request.args.get('type', '')
    filter_priority = request.args.get('priority', '')
    
    query = Notification.query
    
    if filter_type:
        query = query.filter_by(emergency_type=filter_type)
    
    if filter_priority:
        query = query.filter_by(_priority=filter_priority)
    
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    stats = {
        'total': Notification.query.count(),
        'by_type': {},
        'by_priority': {}
    }
    
    for et in EmergencyType:
        count = Notification.query.filter_by(emergency_type=et.value).count()
        stats['by_type'][et.value] = count
    
    for p in Priority:
        count = Notification.query.filter_by(_priority=p.name).count()
        stats['by_priority'][p.name] = count
    
    emergency_types = [e.value for e in EmergencyType]
    priorities = [p.name for p in Priority]
    
    return render_template('dashboard.html', 
                         notifications=notifications, 
                         stats=stats,
                         emergency_types=emergency_types,
                         priorities=priorities,
                         filter_type=filter_type,
                         filter_priority=filter_priority)


@app.route('/admin')
@login_required
def admin():
    """Page d'administration des utilisateurs"""
    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/admin/add-user', methods=['POST'])
@login_required
def add_user():
    """Ajoute un nouvel utilisateur"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        prefers_email = request.form.get('prefers_email') == 'on'
        
        if not all([name, email]):
            flash('Le nom et l\'email sont requis', 'error')
            return redirect(url_for('admin'))
        
        user = User(name=name, email=email, phone=phone if phone else None, prefers_email=prefers_email)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur {name} ajouté avec succès', 'success')
        
    except ValueError as e:
        db.session.rollback()
        flash(f'Erreur de validation: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout: {str(e)}', 'error')
    
    return redirect(url_for('admin'))


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Supprime un utilisateur"""
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash(f'Utilisateur {user.name} supprimé', 'success')
        else:
            flash('Utilisateur introuvable', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin'))


@app.route('/api/notifications')
@login_required
def api_notifications():
    """API pour récupérer les notifications"""
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notifications])


@app.route('/api/stats')
@login_required
def api_stats():
    """API pour les statistiques"""
    stats = {
        'total_notifications': Notification.query.count(),
        'total_users': User.query.count(),
        'by_type': {},
        'by_priority': {},
        'recent_notifications': []
    }
    
    for et in EmergencyType:
        count = Notification.query.filter_by(emergency_type=et.value).count()
        stats['by_type'][et.value] = count
    
    for p in Priority:
        count = Notification.query.filter_by(_priority=p.name).count()
        stats['by_priority'][p.name] = count
    
    recent = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
    stats['recent_notifications'] = [n.to_dict() for n in recent]
    
    return jsonify(stats)


@app.route('/api/performance')
@login_required
def api_performance():
    """API pour récupérer les métriques de performance"""
    metrics = PerformanceMetric.query.order_by(PerformanceMetric.timestamp.desc()).limit(100).all()
    return jsonify([m.to_dict() for m in metrics])


@app.route('/api/queue/status')
@login_required
def queue_status():
    """Récupère le statut de la file d'attente"""
    tasks = []
    for task_id, task in async_queue.tasks.items():
        tasks.append({
            'id': task_id,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'retry_count': task.retry_count,
            'error': task.error,
            'priority': task.priority
        })
    
    return jsonify({
        'queue_size': async_queue.queue.qsize(),
        'total_tasks': len(async_queue.tasks),
        'running_tasks': len([t for t in async_queue.tasks.values() if t.status == TaskStatus.RUNNING]),
        'pending_tasks': len([t for t in async_queue.tasks.values() if t.status == TaskStatus.PENDING]),
        'tasks': tasks
    })


@app.route('/api/queue/clear', methods=['POST'])
@login_required
def clear_queue():
    """Efface la file d'attente"""
    # Arrêt de la file d'attente
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_queue.stop())
        # Réinitialisation
        async_queue.tasks.clear()
        loop.run_until_complete(async_queue.start())
        flash('File d\'attente effacée et redémarrée', 'success')
    except Exception as e:
        flash(f'Erreur lors de l\'effacement de la file d\'attente: {str(e)}', 'error')
    finally:
        loop.close()
    
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Ajout de logs pour le débogage
        print(f"Tentative de connexion - Email: {email}")
        try:
            user = auth_manager.authenticate_user(email, password)
            print(f"Résultat de l'authentification: {user is not None}")
            if user:
                print(f"Authentification réussie pour l'utilisateur: {user.email}, Role: {user.role}")
                # Create session
                token, expires_at = auth_manager.create_user_session(user, user.role)
                
                # Store token in session cookie
                session_token = token
                resp = redirect(url_for('role_redirect'))
                resp.set_cookie('session_token', session_token, httponly=True, secure=False)
                return resp
            else:
                print(f"Échec d'authentification pour l'email: {email}")
                flash('Email ou mot de passe incorrect', 'error')
        except Exception as e:
            import traceback
            print(f"Erreur lors de l'authentification: {str(e)}")
            print(f"Traceback détaillé: {traceback.format_exc()}")
            flash('Erreur lors de l\'authentification', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Déconnexion de l'utilisateur"""
    session_token = request.cookies.get('session_token')
    if session_token:
        auth_manager.session_manager.destroy_session(session_token)
    
    resp = redirect(url_for('index'))
    resp.set_cookie('session_token', '', expires=0)
    return resp


@app.route('/role-redirect')
def role_redirect():
    """Redirection basée sur le rôle de l'utilisateur"""
    session_token = request.cookies.get('session_token')
    if not session_token:
        flash('Veuillez vous connecter', 'error')
        return redirect(url_for('index'))
    
    session_data = auth_manager.validate_user_session(session_token)
    if not session_data:
        flash('Session expirée, veuillez vous reconnecter', 'error')
        return redirect(url_for('login'))
    
    # Rediriger en fonction du rôle
    role = session_data.get('role', 'user')
    if role == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('dashboard'))


def init_db():
    """Initialise la base de données avec des données de test"""
    with app.app_context():
        db.create_all()
        
        # Vérifier si des utilisateurs existent déjà
        if User.query.count() == 0:
            # Créer un utilisateur admin
            admin_user = User(
                name='Admin User',
                email='admin@flashnotify.local',
                phone=None,
                password=auth_manager.hash_password('admin123'),  # Set hashed password directly
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
            print("Base de données initialisée avec des utilisateurs de test")
        else:
            print("Base de données déjà initialisée")
            
        # Pour déboguer : afficher les utilisateurs existants
        all_users = User.query.all()
        print(f"Nombre d'utilisateurs dans la base: {len(all_users)}")
        for user in all_users:
            print(f"User: {user.email}, Role: {user.role}, Password set: {user.password is not None and len(user.password) > 0}")


if __name__ == '__main__':
    init_db()
    init_queues()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        shutdown_queues()
