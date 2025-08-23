import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
SECRET_KEY = secrets.token_hex(16)
