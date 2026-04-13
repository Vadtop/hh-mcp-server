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
            # domcontentloaded быстрее чем networkidle — hh.ru держит соединения
            await page.goto("https://hh.ru", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Кнопка "Войти" — не авторизован
            login_button = page.locator('[data-qa="header-login-button"], [data-qa="header-login"]')
            if await login_button.count() > 0:
                self._is_authenticated = False
                return False

            # Имя пользователя в хедере — авторизован
            user_name = page.locator('[data-qa="header-user-name"], [data-qa="user-name"]')
            if await user_name.count() > 0:
                self._is_authenticated = True
                logger.info("Сессия активна")
                return True

            # Fallback — переход на /applicant/resumes
            await page.goto("https://hh.ru/applicant/resumes", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)

            if "login" in page.url or "account/login" in page.url:
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
        page = await self.browser.new_page()
        
        try:
            logger.info("Переход на страницу входа...")
            await page.goto("https://hh.ru/account/login", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            if not phone:
                phone = input("\n📱 Введите номер телефона (+79XXXXXXXXX): ").strip()

            self._phone = phone
            logger.info(f"Вводим номер: {phone}")

            # Поле телефона — несколько вариантов селектора
            phone_selectors = [
                '[data-qa="login-input-username"]',
                '[data-qa="phone-input"]',
                'input[name="login"]',
                'input[type="tel"]',
                'input[placeholder*="телефон"]',
                'input[placeholder*="Телефон"]',
            ]
            phone_input = None
            for sel in phone_selectors:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    phone_input = loc
                    logger.info(f"Поле телефона: {sel}")
                    break

            if phone_input is None:
                # Делаем скриншот для диагностики
                await page.screenshot(path="auth_debug.png")
                logger.error("Поле телефона не найдено. Скриншот: auth_debug.png")
                return False

            await phone_input.click()
            await phone_input.fill(phone)
            await page.wait_for_timeout(500)

            # Кнопка "Получить код" / "Войти"
            submit_selectors = [
                '[data-qa="account-signup-submit"]',
                '[data-qa="get-code-button"]',
                '[data-qa="login-button"]',
                'button[type="submit"]',
            ]
            submit_btn = None
            for sel in submit_selectors:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    submit_btn = loc
                    logger.info(f"Кнопка отправки: {sel}")
                    break

            if submit_btn is None:
                await page.screenshot(path="auth_debug.png")
                logger.error("Кнопка отправки не найдена. Скриншот: auth_debug.png")
                return False

            await submit_btn.click()

            # Ждём поле кода до 90 сек (SMS может идти долго)
            logger.info("Ожидание поля для SMS-кода...")
            code_selectors = [
                '[data-qa="account-signup-code"]',
                '[data-qa="code-input"]',
                'input[name="code"]',
                'input[placeholder*="код"]',
                'input[placeholder*="Код"]',
            ]
            code_input = None
            for _ in range(30):  # 30 * 3 сек = 90 сек макс
                for sel in code_selectors:
                    loc = page.locator(sel)
                    if await loc.count() > 0:
                        code_input = loc
                        break
                if code_input:
                    break
                await page.wait_for_timeout(3000)

            if code_input is None:
                await page.screenshot(path="auth_debug.png")
                logger.error("Поле SMS-кода не появилось. Скриншот: auth_debug.png")
                return False

            code = input("\n🔐 Введите код из SMS: ").strip()
            if not code:
                logger.error("Код не введён")
                return False

            await code_input.click()
            await code_input.fill(code)
            await page.wait_for_timeout(1000)

            # Кнопка подтверждения кода
            confirm_selectors = [
                '[data-qa="account-signup-submit"]',
                '[data-qa="confirm-button"]',
                'button[type="submit"]',
            ]
            for sel in confirm_selectors:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.click()
                    break

            # Ждём редирект (до 15 сек)
            await page.wait_for_timeout(5000)

            if await self.check_auth():
                logger.info("Авторизация успешна!")
                await self.browser.save_session()
                return True
            else:
                logger.error("Авторизация не удалась")
                await page.screenshot(path="auth_debug.png")
                return False

        except PlaywrightTimeout:
            logger.error("Таймаут при авторизации")
            await page.screenshot(path="auth_debug.png")
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
            await page.goto("https://hh.ru", wait_until="domcontentloaded", timeout=60000)
            
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
