FROM python:3.10-slim

# Установка системных зависимостей, Wine, Xvfb и curl для загрузки файла
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
    wine64 \
    wine32 \
    xvfb \
    curl \
    xdotool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Скачиваем установщик Belbet по прямой ссылке в корень контейнера
RUN curl -L "https://game4.belbet.by/win_installer/setup_belbet_1.2.exe" -o belbet_setup.exe

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 10000

CMD ["python", "server.py"]
