# notifier/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_notifier.py .

CMD ["python", "telegram_notifier.py"]
