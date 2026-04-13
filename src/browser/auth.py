"""
Авторизация на hh.ru через телефон + SMS-код.

Процесс:
1. Открыть страницу входа
2. Ввести номер телефона
3. Подождать SMS-код (вводится вручную)
4. Ввести код подтверждения
5. Сохранить сессию

После авторизации сессия сохраняется в cookies
и восстанавливается при следующем запуске.
"""

import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.browser.engine import BrowserEngine

logger = logging.getLogger(__name__)


class HHAuth:
    """
    Менеджер авторизации hh.ru.
    
    Поддерживает:
    - Интерактивную авторизацию (телефон + SMS)
    - Проверку текущей сессии
    - Повторную авторизацию при истечении сессии
    """
    
    def __init__(self, browser: BrowserEngine):
        self.browser = browser
        self._phone: Optional[str] = None
        self._is_authenticated = False
    
    async def check_auth(self) -> bool:
        """
        Проверяет авторизован ли пользователь.
        
        Returns:
            True если авторизован
        """
        page = await self.browser.new_page()
        
        try:
            # Переходим на главную hh.ru
            await page.goto("https://hh.ru", wait_until="networkidle", timeout=15000)
            
            # Проверяем наличие элемента авторизованного пользователя
            # Если есть кнопка "Войти" — не авторизован
            login_button = page.locator('[data-qa="header-login"]')
            
            if await login_button.count() > 0:
                self._is_authenticated = False
                return False
            
            # Проверяем наличие имени пользователя в хедере
            user_name = page.locator('[data-qa="header-user-name"]')
            if await user_name.count() > 0:
                self._is_authenticated = True
                logger.info("✅ Сессия активна")
                return True
            
            # Альтернативная проверка — переход на /me
            await page.goto("https://hh.ru/me", wait_until="networkidle", timeout=15000)
            
            # Если редирект на /login — не авторизован
            if "login" in page.url:
                self._is_authenticated = False
                return False
            
            self._is_authenticated = True
            return True
            
        except PlaywrightTimeout:
            logger.warning("Таймаут при проверке авторизации")
            self._is_authenticated = False
            return False
        finally:
            await page.close()
    
    async def authenticate(self, phone: Optional[str] = None) -> bool:
        """
        Выполняет интерактивную авторизацию.
        
        Args:
            phone: Номер телефона (если не передан — запросит через input())
            
        Returns:
            True если авторизация успешна
        """
        # Проверяем текущую сессию
        if await self.check_auth():
            return True
        
        page = await self.browser.new_page()
        
        try:
            # Переходим на страницу входа
            logger.info("Переход на страницу входа...")
            await page.goto("https://hh.ru/account/login", wait_until="networkidle", timeout=30000)
            
            # Вводим номер телефона
            if not phone:
                phone = input("\n📱 Введите номер телефона (+79XXXXXXXXX): ").strip()
            
            self._phone = phone
            logger.info(f"Вводим номер: {phone}")
            
            # Находим поле телефона и вводим
            phone_input = page.locator('[data-qa="phone-input"]')
            await phone_input.fill(phone)
            
            # Нажимаем кнопку "Получить код"
            submit_btn = page.locator('[data-qa="get-code-button"]')
            await submit_btn.click()
            
            # Ждём появления поля для кода
            logger.info("⏳ Ожидание SMS-кода...")
            await page.wait_for_selector('[data-qa="code-input"]', timeout=60000)
            
            # Запрашиваем код у пользователя
            code = input("\n🔐 Введите код из SMS: ").strip()
            
            if not code:
                logger.error("Код не введён")
                return False
            
            # Вводим код
            code_input = page.locator('[data-qa="code-input"]')
            await code_input.fill(code)
            
            # Ждём редирект на главную
            await page.wait_for_url("**/hh.ru/**", timeout=30000)
            
            # Проверяем результат
            if await self.check_auth():
                logger.info("✅ Авторизация успешна!")
                
                # Сохраняем сессию
                await self.browser.save_session()
                
                return True
            else:
                logger.error("❌ Авторизация не удалась")
                return False
                
        except PlaywrightTimeout:
            logger.error("Таймаут при авторизации")
            return False
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            return False
        finally:
            await page.close()
    
    async def ensure_authenticated(self) -> bool:
        """
        Гарантирует авторизацию.
        Если сессия истекла — запускает интерактивную авторизацию.
        
        Returns:
            True если авторизован
        """
        if await self.check_auth():
            return True
        
        return await self.authenticate()
    
    async def logout(self):
        """Выход из аккаунта."""
        page = await self.browser.new_page()
        
        try:
            await page.goto("https://hh.ru", wait_until="networkidle")
            
            # Находим меню пользователя и кнопку выхода
            logout_link = page.locator('[data-qa="header-logout"]')
            
            if await logout_link.count() > 0:
                await logout_link.click()
                logger.info("👋 Выход выполнен")
            
            self._is_authenticated = False
            await self.browser.save_session()
            
        except Exception as e:
            logger.error(f"Ошибка при выходе: {e}")
        finally:
            await page.close()
    
    @property
    def phone(self) -> Optional[str]:
        """Возвращает номер телефона."""
        return self._phone
    
    @property
    def is_authenticated(self) -> bool:
        """Проверяет статус авторизации."""
        return self._is_authenticated
