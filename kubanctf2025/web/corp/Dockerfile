FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m app.init_app
EXPOSE 8000
CMD ["flask", "--app", "app.app", "run", "--host=0.0.0.0", "--port=8000"]
