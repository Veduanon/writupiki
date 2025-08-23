from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import pytesseract
from PIL import Image
import cv2

app = Flask(__name__)
app.secret_key = ',mkijqp'
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_valid_upload(f):
    def wrapper(*args, **kwargs):
        if not session.get('upload_valid', False):
            flash('You must upload a valid document first.', 'error')
            return redirect(url_for('apply'))
        return f(*args, **kwargs)
    return wrapper

# Detect stamp using OpenCV
def detect_stamp(uploaded_image_path, stamp_image_path):
    uploaded_image = cv2.imread(uploaded_image_path, cv2.IMREAD_GRAYSCALE)
    stamp_image = cv2.imread(stamp_image_path, cv2.IMREAD_GRAYSCALE)

    result = cv2.matchTemplate(uploaded_image, stamp_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    threshold = 0.8  # Adjust sensitivity
    if max_val >= threshold:
        return True  # Stamp detected
    return False  # Stamp not detected

# Home route
@app.route('/')
def home():
    return render_template('index.html')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    passport_filepath = db.Column(db.String(200))  # File path for passport document
    status = db.Column(db.String(20), default='Pending')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        # Create a new user
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in automatically after registration
        user = User.query.filter_by(username=username).first()
        session['user_id'] = user.id
        session['username'] = user.username
        
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')


# Apply route
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if 'user_id' not in session:
        flash('Please log in to apply for a pass.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        purpose = request.form['purpose']

        # Handle passport document upload
        if 'passport' not in request.files:
            flash('No file uploaded!', 'error')
            return redirect(url_for('apply'))

        file = request.files['passport']
        if file.filename == '':
            flash('No selected file!', 'error')
            return redirect(url_for('apply'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Extract text using Tesseract OCR
                if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                    extracted_text = pytesseract.image_to_string(Image.open(filepath))
                else:
                    raise ValueError("Unsupported file type")

                print(f"Extracted Text: {extracted_text}")

                # Check for the keyword "approved"
                keyword = "approved"
                if keyword.lower() in extracted_text.lower():
                    # Stamp detection
                    stamp_image_path = os.path.join(app.root_path, 'static', 'reference-stamp.png')
                    if detect_stamp(filepath, stamp_image_path):
                        flash('Application approved!', 'success')
                        return render_template('approved.html')
                    else:
                        flash('Application rejected.', 'error')
                        return redirect(url_for('apply'))
                else:
                    flash('Application rejected.', 'error')
                    return redirect(url_for('apply'))

            except Exception as e:
                flash(f'Error processing passport document: {str(e)}', 'error')
                return redirect(url_for('apply'))

        else:
            flash('Invalid file type! Allowed types: png, jpg, jpeg', 'error')

    return render_template('apply.html')

# FAQ route
@app.route('/faq')
def faq():
    return render_template('faq.html')

# Approved route
@app.route('/approved')
@require_valid_upload
def approved():
    return render_template('approved.html')

# Logout route (optional)
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
