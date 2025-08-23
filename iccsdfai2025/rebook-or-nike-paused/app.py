import os
import random
import string
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'very_secret_key'
UPLOAD_FOLDER = './uploads'
TEMPLATE_FOLDER = './templates/music'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

def sanitize_input(value):
    # Block "../" directly, but allow encoded variants
    value = value.replace('..', '')
    return value

def random_string(length=6):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

@app.route('/')
def home():
    songs = []
    for file in os.listdir(TEMPLATE_FOLDER):
        if file.endswith('.html') and not file.startswith('flag'):
            songs.append(file)
    return render_template('home.html', songs=songs)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.mp3'):
        flash('Invalid file type!')
        return redirect(url_for('home'))

    filename = secure_filename(file.filename)
    random_suffix = random_string()
    save_name = filename.replace('.mp3', '') + '_' + random_suffix + '.html'
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    artist = request.form.get('artist', 'Unknown Artist')
    album = request.form.get('album', 'Unknown Album')

    # Very simple sanitization, but can be bypassed by encoding
    artist = sanitize_input(artist)
    album = sanitize_input(album)

    template_content = f"""
    <h1>🎵 New Song Uploaded 🎵</h1>
    <p><strong>Artist:</strong> {artist}</p>
    <p><strong>Album:</strong> {album}</p>
    <p>Check out the magic in our music vaults!</p>
    """

    with open(os.path.join(TEMPLATE_FOLDER, save_name), 'w', encoding='utf-8') as f:
        f.write(template_content)

    flash('Upload successful! Find your song below.')
    return redirect(url_for('home'))

@app.route('/music/<path:song>')
def music(song):
    try:
        # No secure filename here — intentional!
        song = sanitize_input(song)
        return render_template(f'music/{song}')
    except:
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
