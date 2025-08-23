from flask import Flask, render_template, request, jsonify
import random
import string
import uuid
import time

app = Flask(__name__)
app.debug = False

# Configuration
ADMIN_ID = 1000
FLAG = "CTF{temp_m41l_0bfusc4t3d_3ndp01nt}"
API_SECRET = "x-tm-admin-" + str(uuid.uuid4())
REQUEST_DELAY = 0.5

# In-memory storage
users_db = {
    "admin": {
        "id": ADMIN_ID,
        "email": None,
        "secret": API_SECRET
    }
}

# Generate 50 random emails
email_pool = [f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}@tempmailclone.com" 
              for _ in range(50)]

# Welcome email template
WELCOME_EMAIL = {
    "subject": "Account Created Successfully 🎉",
    "body": "Your temporary email address is ready to use.",
    "timestamp": "Just now"
}

# Initialize inboxes
inboxes = {}
admin_email = random.choice(email_pool)

for email in email_pool:
    inboxes[email] = [WELCOME_EMAIL.copy()]
    
    if email == admin_email:
        inboxes[email].append({
            "subject": "System Maintenance Notification",
            "body": f"Critical security update. Flag: {FLAG}",
            "timestamp": "5 min ago"
        })
    else:
        inboxes[email].extend([
            {
                "subject": "Welcome Bonus Inside!",
                "body": "Claim your special offer now!",
                "timestamp": f"{random.randint(1, 60)} min ago"
            },
            {
                "subject": "Password Reset Request",
                "body": "Click here to reset your password",
                "timestamp": f"{random.randint(1, 60)} min ago"
            }
        ])

# Hidden API endpoint decorator
def hidden_api(f):
    def wrapper(*args, **kwargs):
        if request.headers.get('X-TM-Key') != API_SECRET:
            time.sleep(REQUEST_DELAY)
            return jsonify({"error": "Not found"}), 404
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-email', methods=['POST'])
def generate_email():
    email = random.choice(email_pool)
    return jsonify({"email": email})

# Fixed endpoint
@app.route('/api/inbox', methods=['GET'])
def get_inbox():
    email = request.args.get('email')
    return jsonify({"emails": inboxes.get(email, [])})

# Hidden admin endpoint
@app.route('/.well-known/tm-admin', methods=['GET'])
@hidden_api
def get_admin():
    return jsonify({
        "users": [{
            "id": users_db["admin"]["id"],
            "email": admin_email,
            "username": "admin"
        }]
    })

if __name__ == '__main__':
    print(f"[DEBUG] Admin email: {admin_email}")
    app.run(port=5000)