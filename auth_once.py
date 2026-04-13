"""
Авторизация на hh.ru один раз.
Запускать ОТДЕЛЬНО от MCP сервера, в обычном терминале:

    cd c:\portfolio_2026\hh_mcp_server_v2
    python auth_once.py

После успешной авторизации сессия сохранится в .browser_session/
и MCP сервер будет использовать её автоматически.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth


async def main():
    print("=" * 50)
    print("  Авторизация hh.ru (один раз)")
    print("=" * 50)
    print()
    print("Браузер откроется в ВИДИМОМ режиме.")
    print("Введи телефон и SMS-код когда попросит.")
    print()

    # headless=False — браузер видимый
    browser = BrowserEngine(headless=False, slow_mo=100)

    try:
        await browser.start()
        auth = HHAuth(browser)

        # Проверяем — может сессия уже есть
        print("Проверяю текущую сессию...")
        if await auth.check_auth():
            print()
            print("✅ Сессия уже активна! Авторизация не нужна.")
            print("   MCP сервер готов к работе.")
            return

        print("Сессии нет. Начинаю авторизацию...")
        print()

        # Авторизуемся (auth.py вызовет input() — это нормально в терминале)
        success = await auth.authenticate()

        if success:
            print()
            print("✅ Авторизация успешна!")
            print(f"   Сессия сохранена в: {browser.user_data_dir}")
            print()
            print("Теперь запускай MCP сервер через Cline — всё будет работать.")
        else:
            print()
            print("❌ Авторизация не удалась.")
            print("   Попробуй ещё раз или проверь номер телефона.")

    except KeyboardInterrupt:
        print("\nОтменено.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
