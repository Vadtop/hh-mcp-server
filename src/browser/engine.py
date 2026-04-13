"""
Playwright Browser Engine.

Управляет браузером Chromium для автоматизации hh.ru:
- Запуск/закрытие браузера
- Управление страницами
- Сохранение/загрузка сессии (cookies/storage)
- Контекст браузера с настройками анти-детекта
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from src.config import BASE_DIR

logger = logging.getLogger(__name__)


class BrowserEngine:
    """
    Менеджер Playwright браузера.
    
    Отвечает за:
    - Инициализацию браузера
    - Сохранение сессии (cookies, localStorage)
    - Восстановление сессии при перезапуске
    - Создание новых страниц (tab)
    - Корректное закрытие
    """
    
    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 50,
        timeout: int = 30000,
        user_data_dir: Optional[str] = None,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        
        # Директория для сохранения сессии
        self.user_data_dir = user_data_dir or str(BASE_DIR / ".browser_session")
        
        # Playwright объекты
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
        # Флаг инициализации
        self._initialized = False
    
    async def start(self) -> BrowserContext:
        """
        Запускает браузер и возвращает контекст.
        
        Returns:
            BrowserContext для работы со страницами
        """
        if self._initialized:
            return self._context
        
        logger.info("Запуск браузера...")
        
        # Создаём директорию для сессии
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        
        # Запускаем Playwright
        self._playwright = await async_playwright().start()
        
        # Запускаем Chromium
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        
        # Загружаем сохранённую сессию
        storage_state = self._load_storage_state()

        # Фиксированный user-agent — случайный ломает сессию (hh.ru привязывает к UA)
        fixed_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

        # Создаём контекст
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=fixed_ua,
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            storage_state=storage_state,
            ignore_https_errors=True,
        )
        
        # Устанавливаем таймаут
        self._context.set_default_timeout(self.timeout)
        
        self._initialized = True
        logger.info("Браузер запущен")
        
        return self._context
    
    async def new_page(self) -> Page:
        """
        Создаёт новую страницу.
        
        Returns:
            Page объект
        """
        if not self._context:
            await self.start()
        
        page = await self._context.new_page()
        return page
    
    async def save_session(self):
        """Сохраняет cookies и localStorage."""
        if not self._context:
            return
        
        try:
            storage = await self._context.storage_state()
            
            storage_path = Path(self.user_data_dir) / "storage.json"
            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(storage, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Сессия сохранена: {storage_path}")
        except Exception as e:
            logger.warning(f"Ошибка сохранения сессии: {e}")
    
    def _load_storage_state(self) -> Optional[dict]:
        """Загружает cookies и localStorage из файла."""
        storage_path = Path(self.user_data_dir) / "storage.json"
        
        if storage_path.exists():
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    storage = json.load(f)
                
                cookies = storage.get("cookies", [])
                if cookies:
                    logger.info(f"Загружено {len(cookies)} cookies из сессии")
                    return storage
            except Exception as e:
                logger.warning(f"Ошибка загрузки сессии: {e}")
        
        return None
    
    def _get_user_agent(self) -> str:
        """Генерирует User-Agent."""
        import random
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        ]
        
        return random.choice(user_agents)
    
    async def close(self):
        """Закрывает браузер с сохранением сессии."""
        if self._context:
            await self.save_session()
            await self._context.close()
        
        if self._browser and not self._browser.is_connected():
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        self._initialized = False
        logger.info("Браузер закрыт")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @property
    def is_running(self) -> bool:
        """Проверяет запущен ли браузер."""
        return self._initialized and self._context is not None
    
    @property
    def context(self) -> Optional[BrowserContext]:
        """Возвращает контекст браузера."""
        return self._context
