FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium y Chromedriver desde Debian
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    chromium chromium-driver \
    libnss3 libxi6 libxcursor1 libxcomposite1 \
    libasound2 libxrandr2 libxtst6 libatk1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "main.py"]