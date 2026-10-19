// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const statusDiv = document.getElementById('status');

// WSS-адрес вашего локального сервера (получим на Этапе 4)
const WS_URL = 'wss://belbet-production.up.railway.app';

let socket = null;
const DESKTOP_WIDTH = 1280;
const DESKTOP_HEIGHT = 720;
function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        statusDiv.innerText = 'Подключено к серверу';
        statusDiv.style.color = '#00ff00';
    };

    socket.onmessage = (event) => {
        // Получение очередного кадра с сервера
        const image = new Image();
        image.onload = () => {
            canvas.width = image.width;
            canvas.height = image.height;
            ctx.drawImage(image, 0, 0);
        };
        image.src = event.data;
    };

    socket.onclose = () => {
        statusDiv.innerText = 'Соединение разорвано. Переподключение...';
        statusDiv.style.color = '#ff0000';
        setTimeout(connect, 2000);
    };

    socket.onerror = (err) => {
        console.error('WebSocket Error:', err);
    };
}

// Перехват клика/касания и математический пересчет координат
function handleTouch(e) {
    e.preventDefault();
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    // Формула пересчета координат клика с экрана iPhone на разрешение ПК (1920x1080)
    const scaleX = DESKTOP_WIDTH / rect.width;
    const scaleY = DESKTOP_HEIGHT / rect.height;

    const targetX = Math.round((clientX - rect.left) * scaleX);
    const targetY = Math.round((clientY - rect.top) * scaleY);

    // Отправка координат на ПК-сервер
    socket.send(JSON.stringify({
        type: 'click',
        x: targetX,
        y: targetY
    }));
}

canvas.addEventListener('touchstart', handleTouch, { passive: false });
canvas.addEventListener('mousedown', handleTouch);

connect();
