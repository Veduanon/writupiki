FROM node:18

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только package.json и package-lock.json сначала (оптимизация слоёв кеша)
COPY package*.json ./

# Устанавливаем зависимости без сохранения мусора
RUN npm install --production

# Теперь копируем оставшийся код
COPY . .

# Открываем порт
EXPOSE 33400

# Дефолтная команда запуска приложения
CMD ["node", "lastServer.js"]
