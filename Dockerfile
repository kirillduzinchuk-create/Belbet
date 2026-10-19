FROM python:3.10-slim

# Установка системных зависимостей для Headless Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir websockets playwright pillow
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . /app

EXPOSE 10000

CMD ["python", "server.py"]
