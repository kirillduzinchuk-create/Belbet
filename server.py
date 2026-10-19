import asyncio
import websockets
import json
import base64
import os
import aiohttp
from playwright.async_api import async_playwright

BOT_TOKEN = "8830963907:AAGA0dGrzrDwADGqUGU2s3MAr0D1oDmmGZI"
WEB_APP_URL = "https://kirillduzinchuk-create.github.io/Belbet/"

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

connected_clients = set()
page_instance = None
current_status = "Инициализация..."

async def update_visual_status(text):
    global current_status, page_instance
    current_status = text
    print(f"[STATUS]: {text}")
    if page_instance:
        try:
            await page_instance.evaluate(f"""
                (statusText) => {{
                    let banner = document.getElementById('debug-status-banner');
                    if (!banner) {{
                        banner = document.createElement('div');
                        banner.id = 'debug-status-banner';
                        banner.style.position = 'fixed';
                        banner.style.top = '10px';
                        banner.style.left = '50%';
                        banner.style.transform = 'translateX(-50%)';
                        banner.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
                        banner.style.color = '#00FF66';
                        banner.style.padding = '8px 18px';
                        banner.style.borderRadius = '20px';
                        banner.style.fontSize = '16px';
                        banner.style.fontFamily = 'monospace, sans-serif';
                        banner.style.fontWeight = 'bold';
                        banner.style.zIndex = '9999999';
                        banner.style.border = '2px solid #00FF66';
                        banner.style.pointerEvents = 'none';
                        document.body.appendChild(banner);
                    }}
                    banner.innerText = statusText;
                }}
            """, text)
        except Exception:
            pass

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

async def handle_client(websocket, path=None):
    global page_instance
    connected_clients.add(websocket)
    await update_visual_status("Клиент подключен!")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'click' and page_instance:
                x = data.get('x')
                y = data.get('y')
                await update_visual_status(f"Клик: ({x}, {y})")
                await page_instance.mouse.click(x, y)
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)

async def stream_screen():
    global page_instance
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        context = await browser.new_context(
            viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ru-BY",
            geolocation={"latitude": 53.9006, "longitude": 27.5590},
            permissions=["geolocation"]
        )
        page_instance = await context.new_page()
        
        await update_visual_status("Быстрый старт Belbet...")
        try:
            # Загружаем страницу не дожидаясь всех тяжелых скриптов и шрифтов
            await page_instance.goto("https://belbet.by/games", wait_until="domcontentloaded", timeout=30000)
            await update_visual_status("Сайт открыт!")
        except Exception as e:
            await update_visual_status(f"Загружено с ограничением: {e}")

        frame_count = 0
        while True:
            if connected_clients and page_instance:
                try:
                    frame_count += 1
                    # Оптимизированный скриншот с минимальным разрешением и высокой сжимаемостью
                    screenshot_bytes = await page_instance.screenshot(type="jpeg", quality=30)
                    base64_frame = "data:image/jpeg;base64," + base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    for client in list(connected_clients):
                        await client.send(base64_frame)
                except Exception as e:
                    print(f"Ошибка скриншота: {e}")
            
            # Оптимальная задержка для стабильности Railway
            await asyncio.sleep(0.2)

async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"Облачный WS-сервер запущен на порту {port}...")
        await asyncio.gather(
            stream_screen(),
            telegram_bot_polling()
        )

if __name__ == "__main__":
    asyncio.run(main())
