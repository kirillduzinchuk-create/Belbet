import asyncio
import websockets
import json
import base64
import os
import subprocess
import aiohttp
from mss import mss
from PIL import Image
import io

BOT_TOKEN = "8830963907:AAGA0dGrzrDwADGqUGU2s3MAr0D1oDmmGZI"
WEB_APP_URL = "https://kirillduzinchuk-create.github.io/Belbet/"

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

connected_clients = set()
app_process = None
current_status = "Инициализация Wine и запуск приложения..."

async def update_visual_status(text):
    global current_status
    current_status = text
    print(f"[STATUS]: {text}")

async def telegram_bot_polling():
    offset = 0
    async with aiohttp.ClientSession() as session:
        print("Telegram бот запущен...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for update in data.get("result", []):
                            offset = update["update_id"] + 1
                            message = update.get("message")
                            if message and "text" in message:
                                chat_id = message["chat"]["id"]
                                text = message["text"]
                                if text.startswith("/start"):
                                    payload = {
                                        "chat_id": chat_id,
                                        "text": "Интерфейс Belbet App готов:",
                                        "reply_markup": {
                                            "inline_keyboard": [[
                                                {
                                                    "text": "🎮 Запустить приложение",
                                                    "web_app": {"url": WEB_APP_URL}
                                                }
                                            ]]
                                        }
                                    }
                                    await session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
            except Exception as e:
                print(f"Ошибка в Telegram боте: {e}")
            await asyncio.sleep(1)

async def handle_client(websocket, path=None):
    connected_clients.add(websocket)
    await update_visual_status("Клиент подключен к сессии!")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'click':
                x = data.get('x')
                y = data.get('y')
                print(f"Клик по координатам приложения: X={x}, Y={y}")
                # Передаем клик мыши в виртуальный дисплей на базе xdotool
                subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)

async def stream_app_screen():
    global app_process
    
    # Настраиваем виртуальный дисплей Xvfb
    os.environ["DISPLAY"] = ":99"
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", f"{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}x24"])
    await asyncio.sleep(3)
    
    print("Установка/запуск приложения Belbet через Wine...")
    # Сначала пытаемся запустить установщик в тихом режиме или запускаем уже распакованный бинарник
    app_process = subprocess.Popen(["wine", "belbet_setup.exe"])
    await update_visual_status("Приложение запущенно в Wine, идет стриминг...")

    with mss() as sct:
        monitor = {"top": 0, "left": 0, "width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        while True:
            if connected_clients:
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=55)
                    screenshot_bytes = buffer.getvalue()
                    
                    base64_frame = "data:image/jpeg;base64," + base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    for client in list(connected_clients):
                        await client.send(base64_frame)
                except Exception as e:
                    print(f"Ошибка стриминга кадра: {e}")
            
            await asyncio.sleep(0.15)

async def main():
    port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"Сервер управления запущен на порту {port}...")
        await asyncio.gather(
            stream_app_screen(),
            telegram_bot_polling()
        )

if __name__ == "__main__":
    asyncio.run(main())
