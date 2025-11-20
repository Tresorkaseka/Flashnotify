from app import app, db
from models import User

with app.app_context():
    print('Nombre d\'utilisateurs:', User.query.count())
    users = User.query.all()
    for u in users:
        print(f'{u.email} - {u.role} - ID: {u.id}')