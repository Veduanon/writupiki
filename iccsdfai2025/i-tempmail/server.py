from flask import Flask, jsonify

app = Flask(__name__)

users = [
    {"id": 0, "email": "admin_88a1@temp-mail.ctf", "username": "admin"},
    {"id": 1, "email": "user1@example.com", "username": "user1"}
]

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # IDOR Vulnerability: No authorization check
    user = next((u for u in users if u['id'] == user_id), None)
    return jsonify(user) if user else ('Not found', 404)

if __name__ == '__main__':
    app.run(port=5000)