"""
Открывает браузер — войди вручную на hh.ru, потом нажми Enter.
Сессия сохранится автоматически.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.browser.engine import BrowserEngine


async def main():
    print("Открываю браузер...")
    browser = BrowserEngine(headless=False, slow_mo=50)
    await browser.start()

    page = await browser.new_page()
    await page.goto("https://hh.ru/account/login", wait_until="domcontentloaded")

    print()
    print("Войди на hh.ru в открывшемся браузере.")
    print("Когда окажешься на главной странице — нажми Enter здесь.")
    input(">>> ")

    await browser.save_session()
    print("Сессия сохранена!")

    await page.close()
    await browser.close()


asyncio.run(main())
