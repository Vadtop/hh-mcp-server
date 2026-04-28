"""
A.4: Контекстный менеджер для безопасной работы со страницами.

Решает утечку Page при таймаутах new_page().
Используется во всех сервисах вместо ручного try/finally/close.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from src.browser.engine import BrowserEngine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def safe_page(
    browser: BrowserEngine,
    timeout: float = 15.0,
) -> AsyncGenerator:
    page = None
    try:
        page = await asyncio.wait_for(browser.new_page(), timeout=timeout)
        yield page
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
