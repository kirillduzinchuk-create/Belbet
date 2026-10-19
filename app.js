// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const statusDiv = document.getElementById('status');

// Ваш актуальный адрес на Railway
const WS_URL = 'wss://belbet-production.up.railway.app';

// Фиксированное разрешение облачного браузера
const DESKTOP_WIDTH = 1280;
const DESKTOP_HEIGHT = 720;

let ws = null;

function connect() {
    statusDiv.innerText = 'Подключение к серверу...';
    statusDiv.style.color = '#FFA500';
    
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        statusDiv.innerText = 'Подключено';
        statusDiv.style.color = '#00FF00';
    };

    ws.onmessage = (event) => {
        // Получение кадра с сервера
        const image = new Image();
        image.onload = () => {
            canvas.width = DESKTOP_WIDTH;
            canvas.height = DESKTOP_HEIGHT;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
        };
        image.src = event.data;
    };

    ws.onclose = () => {
        statusDiv.innerText = 'Соединение разорвано. Переподключение...';
        statusDiv.style.color = '#FF0000';
        setTimeout(connect, 2000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket ошибка:', error);
        ws.close();
    };
}

// Обработка нажатий (кликов) по экрану телефона
canvas.addEventListener('click', (event) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = DESKTOP_WIDTH / rect.width;
    const scaleY = DESKTOP_HEIGHT / rect.height;

    const x = Math.round((event.clientX - rect.left) * scaleX);
    const y = Math.round((event.clientY - rect.top) * scaleY);

    ws.send(JSON.stringify({ type: 'click', x: x, y: y }));
});

// Поддерживаем также тапы на мобильных устройствах
canvas.addEventListener('touchstart', (event) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const touch = event.touches[0];
    const rect = canvas.getBoundingClientRect();
    const scaleX = DESKTOP_WIDTH / rect.width;
    const scaleY = DESKTOP_HEIGHT / rect.height;

    const x = Math.round((touch.clientX - rect.left) * scaleX);
    const y = Math.round((touch.clientY - rect.top) * scaleY);

    ws.send(JSON.stringify({ type: 'click', x: x, y: y }));
    event.preventDefault();
});

connect();
