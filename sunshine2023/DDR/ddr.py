from pwn import *

# Установите адрес и порт, на котором работает игра
remote_host = 'chal.2023.sunshinectf.games'
remote_port = 23200

# Создайте соединение с игрой
io = remote(remote_host, remote_port)
print(io.recv().decode('utf-8'))
# Функция для решения задачи
io.sendline(b'')

keys = {
    'w': '⇧',
    'a': '⇦',
    's': '⇩',
    'd': '⇨'
}

while True:
    response = io.recv()
    print(response)

    if b'flag' in response:
        break

    if b'Press ENTER To Start' in response:
        io.sendline(b'')
        for key, arrow in keys.items():
            if arrow.encode() in response:
                io.send(key.encode)
                break
