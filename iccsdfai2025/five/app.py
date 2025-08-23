from flask import Flask, render_template, request, jsonify, make_response
import hashlib
import os

app = Flask(__name__)

# Generate random flag per instance
FLAG = os.environ.get('FLAG', 'ICTF{0p3n_s3s4m3}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    password = request.form.get('password', '')
    
    # Calculate lengths
    char_length = len(password)
    byte_length = len(password.encode('utf-8'))
    
    # Security checks
    hash_valid = (
        request.form.get('hash', '') == 
        hashlib.sha256(password.encode()).hexdigest()
    )
    
    is_valid = (
        char_length <= 4 and
        byte_length >= 5 and
        hash_valid
    )
    
    response = {
        'success': is_valid,
        'message': FLAG if is_valid else "Keep trying!",
        'debug': {
            'chars': char_length,
            'bytes': byte_length,
            'hash_valid': hash_valid
        }
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)