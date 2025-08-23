import os
import secrets
from werkzeug.security import generate_password_hash
from app.models import db, User, File
from app.config import DB_PATH
from flask import Flask

def init_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STORAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'storage')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        admin_pass = secrets.token_hex(8)
        admin = User(username='admin', password=generate_password_hash(admin_pass), is_admin=True)
        db.session.add(admin)
        db.session.commit()

        admin_file_id = secrets.token_hex(6)

        os.makedirs(STORAGE_DIR, exist_ok=True)

        flag = 'CSC{F4K3_FL4G}'
        flag_path = os.path.join(STORAGE_DIR, f'{admin_file_id}.txt')

        with open(flag_path, 'w') as f:
            f.write(flag)

        db.session.add(File(owner_id=admin.id, file_id=admin_file_id, filename='secret.txt', path=flag_path))
        db.session.commit()

        print(f'[+] Admin password: {admin_pass}')

if __name__ == '__main__':
    init_database()
