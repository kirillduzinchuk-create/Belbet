const WS_URL = 'ws://194.36.88.42:8080';
let ws;
const imgElement = document.getElementById('screen');

function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('[+] Подключено к стриму Windows');
    };

    ws.onmessage = (event) => {
        // Получаем кадр в формате base64 от сервера и выводим в тег <img>
        if (imgElement) {
            imgElement.src = event.data;
        }
    };

    ws.onclose = () => {
        console.log('[-] Разрыв соединения. Переподключение...');
        setTimeout(connect, 2000);
    };
}

// Обработка кликов с телефона по экрану трансляции
window.addEventListener('DOMContentLoaded', () => {
    connect();

    if (imgElement) {
        imgElement.addEventListener('click', (e) => {
            const rect = imgElement.getBoundingClientRect();
            const clientX = e.clientX - rect.left;
            const clientY = e.clientY - rect.top;

            // Пересчитываем координаты под базовое разрешение сервера (1280x720)
            const scaleX = 1280 / imgElement.clientWidth;
            const scaleY = 720 / imgElement.clientHeight;

            const x = Math.round(clientX * scaleX);
            const y = Math.round(clientY * scaleY);

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'click', x: x, y: y }));
            }
        });
    }
});
