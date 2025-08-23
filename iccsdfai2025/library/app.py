from flask import Flask
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

app = Flask(__name__)

# Генерация RSA ключей
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Сохраняем публичный ключ в PEM формате
pub_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Флаг
FLAG = "CODEBY{FAKE_FLAG}"  # Настоящий флаг будет в системе

@app.route('/get_pub')
def get_pub():
    return pub_pem.decode('utf-8'), 200, {'Content-Type': 'text/plain'}

@app.route('/gen-jwt/<username>')
def generate_jwt(username):
    # Создание payload с указанным именем пользователя
    payload = {
        "isAdmin": False,
        "name": username
    }
    
    # Генерация токена с алгоритмом RS256
    token = jwt.encode(
        payload,
        private_key,
        algorithm='RS256',
        headers={'typ': 'JWT', 'alg': 'RS256'}
    )
    
    return {'token': token}, 200

@app.route('/check-jwt/<string:token>')
def check_jwt(token):
    try:
        # УЯЗВИМОСТЬ: Не проверяем алгоритм явно
        decoded = jwt.decode(
            token,
            pub_pem,
            algorithms=['HS256', 'RS256']  # Разрешаем оба алгоритма
        )
        
        if decoded.get('isAdmin'):
            return {'message': f'Access granted! Flag: {FLAG}'}, 200
        else:
            return {'message': 'Access denied! Not an admin'}, 403
            
    except Exception as e:
        return {'error': str(e)}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)