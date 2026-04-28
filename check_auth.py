"""Check if hh.ru session is alive."""
import asyncio
from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth

async def main():
    browser = BrowserEngine(headless=False, slow_mo=100)
    await browser.start()
    auth = HHAuth(browser)

    is_auth = await auth.check_auth()
    status = "SESSION ACTIVE" if is_auth else "SESSION EXPIRED"
    print(f"\n{status}")

    await asyncio.sleep(5)
    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
