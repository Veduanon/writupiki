import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, abort, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, File
from app.config import DB_PATH

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'storage')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.secret_key = secrets.token_hex(16)

db.init_app(app)


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('upload.html', error="File is too large (max 5 MB)."), 413

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    files = File.query.filter_by(owner_id=user.id).all()
    return render_template('dashboard.html', user=user, files=files)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', error='No file part')
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return render_template('upload.html', error='No selected file')
        filename = secure_filename(uploaded_file.filename)
        file_id = secrets.token_hex(6)
        save_filename = f"{file_id}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        uploaded_file.save(save_path)
        new_file = File(owner_id=session['user_id'], file_id=file_id, filename=filename, path=save_path)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('upload.html')


@app.route('/file/<file_id>')
def download_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    file = File.query.filter_by(file_id=file_id).first()
    if not file or not os.path.isfile(file.path):
        abort(404)
    return send_file(file.path, as_attachment=True)


@app.route('/api/files')
def api_files():
    user_ids = request.args.getlist('user_id')

    if len(user_ids) == 1:
        target_user_id = user_ids[0]
    elif len(user_ids) > 1:
        target_user_id = user_ids[0]
        check_user_id = user_ids[-1]
    else:
        target_user_id = session.get('user_id')
        check_user_id = session.get('user_id')

    if user_ids:
        check_user_id = user_ids[-1]
    else:
        check_user_id = session.get('user_id')

    if str(check_user_id) != str(session.get('user_id')):
        return {"error": "Access denied"}, 403

    files = File.query.filter_by(owner_id=target_user_id).all()
    return {
        "files": [
            {"filename": f.filename, "file_id": f.file_id}
            for f in files
        ]
    }



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
