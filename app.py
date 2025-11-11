"""
Application Flask principale - Système de Notification Académique
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Notification, PerformanceMetric
from core.notification_system import AcademicNotifier, EmergencyType, Priority, get_priority
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///notifications.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

notifier = AcademicNotifier()


@app.route('/')
def index():
    """Page d'accueil avec formulaire d'envoi de notification"""
    users = User.query.all()
    emergency_types = [e.value for e in EmergencyType]
    return render_template('index.html', users=users, emergency_types=emergency_types)


@app.route('/send-notification', methods=['POST'])
def send_notification():
    """Envoie une notification"""
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
        
        user_dict = user.to_dict()
        
        notification_data = notifier.notify(user_dict, title, body, emergency_type)
        
        priority = get_priority(emergency_type)
        channels = ', '.join([r['channel'] for r in notification_data['results'] if r])
        
        notification = Notification(
            user_id=user.id,
            title=title,
            body=body,
            emergency_type=emergency_type.value,
            priority=priority.name,
            channels=channels,
            status='sent'
        )
        db.session.add(notification)
        
        metrics = notifier.get_performance_metrics()
        for metric in metrics:
            perf = PerformanceMetric(
                method_name=metric['method'],
                duration=metric['duration'],
                timestamp=metric['timestamp']
            )
            db.session.add(perf)
        
        db.session.commit()
        
        notifier._performance_metrics.clear()
        
        flash(f'Notification envoyée avec succès à {user.name} (Priorité: {priority.name})', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'envoi: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/dashboard')
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
def admin():
    """Page d'administration des utilisateurs"""
    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/admin/add-user', methods=['POST'])
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
def api_notifications():
    """API pour récupérer les notifications"""
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notifications])


@app.route('/api/stats')
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


def init_db():
    """Initialise la base de données avec des données de test"""
    with app.app_context():
        db.create_all()
        
        if User.query.count() == 0:
            users = [
                User(name='Alice Martin', email='alice.martin@universite.edu', phone='+33612345678', prefers_email=True),
                User(name='Bob Dupont', email='bob.dupont@universite.edu', phone='+33623456789', prefers_email=False),
                User(name='Charlie Bernard', email='charlie.bernard@universite.edu', prefers_email=True),
            ]
            
            for user in users:
                db.session.add(user)
            
            db.session.commit()
            print("✓ Base de données initialisée avec des utilisateurs de test")
        else:
            print("✓ Base de données déjà initialisée")


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
