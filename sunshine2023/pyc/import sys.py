import socket
import re
import time
import random

# Функция для ввода стрелок
def input_arrow(direction, conn):
    conn.send(direction.encode())
    time.sleep(0.5)

# Функция для получения случайной последовательности стрелок от сервера
def get_random_arrow_sequence(conn):
    conn.send(b"get_random_arrow_sequence\n")
    response = conn.recv(1024).decode()
    # Парсинг ответа сервера, который должен быть в формате "Arrows: ⇩⇨⇧⇧⇨⇩..."
    match = re.search(r"Arrows: (.+)\n", response)
    if match:
        return match.group(1)
    else:
        return None

# Подключение к серверу
host = "chal.2023.sunshinectf.games"
port = 23200

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
    conn.connect((host, port))
    conn.recv(1024)  # Ожидание приветствия

    # Основной цикл
    while True:
        # Получение случайной последовательности стрелок
        arrow_sequence = get_random_arrow_sequence(conn)
        
        if arrow_sequence:
            print("Received Arrow Sequence:", arrow_sequence)
            
            # Проход по последовательности и ввод клавиш
            for arrow in arrow_sequence:
                if arrow == "⇩":
                    input_arrow("s", conn)
                elif arrow == "⇨":
                    input_arrow("d", conn)
                elif arrow == "⇧":
                    input_arrow("w", conn)
                elif arrow == "⇦":
                    input_arrow("a", conn)
            
            # Получение ответа от сервера
            response = conn.recv(1024).decode()
            print(response)
        
        # Пауза перед получением новой последовательности
        time.sleep(1)
