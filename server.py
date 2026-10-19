import asyncio
import websockets
import json
import base64
import os
import aiohttp
from playwright.async_api import async_playwright

# Конфигурация
BOT_TOKEN = "8830963907:AAGA0dGrzrDwADGqUGU2s3MAr0D1oDmmGZI"
WEB_APP_URL = "https://kirillduzinchuk-create.github.io/Belbet/"

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

connected_clients = set()
page_instance = None

# --- ФОНОВЫЙ ПОТОК TELEGRAM БОТА ---
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
                                        "text": "Добро пожаловать! Нажмите кнопку ниже, чтобы запустить игру:",
                                        "reply_markup": {
                                            "inline_keyboard": [[
                                                {
                                                    "text": "🎮 Играть в Belbet",
                                                    "web_app": {"url": WEB_APP_URL}
                                                }
                                            ]]
                                        }
                                    }
                                    await session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
            except Exception as e:
                print(f"Ошибка в Telegram боте: {e}")
            await asyncio.sleep(1)

# --- WEBSOCKET И СТРИМИНГ ---
async def handle_client(websocket, path=None):
    global page_instance
    connected_clients.add(websocket)
    print("Мини-приложение подключилось к облаку.")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'click' and page_instance:
                x = data.get('x')
                y = data.get('y')
                print(f"Клик на облачном сервере: ({x}, {y})")
                await page_instance.mouse.click(x, y)
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print("Мини-приложение отключилось.")

async def stream_screen():
    global page_instance
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = await browser.new_context(
            viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page_instance = await context.new_page()
        
        print("Загрузка Belbet...")
        try:
            await page_instance.goto("https://belbet.by/games", timeout=60000)
        except Exception as e:
            print(f"Ошибка загрузки страницы: {e}")

        while True:
            if connected_clients and page_instance:
                try:
                    screenshot_bytes = await page_instance.screenshot(type="jpeg", quality=40)
                    base64_frame = "data:image/jpeg;base64," + base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    for client in list(connected_clients):
                        await client.send(base64_frame)
                except Exception as e:
                    print(f"Ошибка отправки кадра: {e}")
            
            await asyncio.sleep(0.08)

async def main():
    port = int(os.environ.get("PORT", 8080))
    # В websockets v10+ параметр path не передается, поэтому запускаем с 0.0.0.0
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"Облачный WS-сервер запущен на порту {port}...")
        await asyncio.gather(
            stream_screen(),
            telegram_bot_polling()
        )

if __name__ == "__main__":
    asyncio.run(main())
