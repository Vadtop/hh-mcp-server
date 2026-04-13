"""
Анти-детект меры.

Имитирует поведение реального пользователя:
- Рандомные задержки между действиями
- Человеческий скролл
- Рандомизация движения мыши
- Обработка капчи
"""

import random
import asyncio
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class AntiDetect:
    """
    Меры по обходу детекции автоматизации.
    """
    
    @staticmethod
    async def random_delay(min_sec: float = 1.0, max_sec: float = 4.0):
        """
        Рандомная пауза между действиями.
        """
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def human_scroll(page: Page, distance: int = None):
        """
        Имитирует человеческий скролл.
        """
        if distance is None:
            distance = random.randint(300, 800)
        
        # Скроллим частями с паузами
        steps = random.randint(3, 7)
        step_distance = distance // steps
        
        for _ in range(steps):
            await page.evaluate(f"window.scrollBy(0, {step_distance})")
            await asyncio.sleep(random.uniform(0.1, 0.4))
    
    @staticmethod
    async def remove_automation_indicators(page: Page):
        """
        Удаляет признаки автоматизации из страницы.
        """
        try:
            await page.evaluate("""
                () => {
                    // Удаляем webdriver
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    
                    // Подделываем chrome.runtime
                    window.chrome = { runtime: {} };
                    
                    // Удаляем признаки headless
                    delete navigator.__proto__.webdriver;
                }
            """)
        except Exception as e:
            logger.warning(f"Не удалось удалить индикаторы: {e}")
    
    @staticmethod
    async def handle_captcha(page: Page) -> bool:
        """
        Проверяет наличие капчи и ждёт ручного прохождения.
        
        Returns:
            True если капча пройдена
        """
        try:
            # Проверяем наличие hcaptcha/recaptcha
            captcha_selectors = [
                '[data-qa="captcha"]',
                '.hcaptcha-container',
                '.g-recaptcha',
                '#hcaptcha-container',
            ]
            
            for selector in captcha_selectors:
                captcha = page.locator(selector)
                if await captcha.count() > 0:
                    logger.warning("⚠️ Обнаружена капча!")
                    print("\n⚠️ Пожалуйста, пройдите капчу в браузере...")
                    
                    # Ждём пока капча исчезнет
                    await page.wait_for_selector(selector, state="hidden", timeout=120000)
                    
                    logger.info("✅ Капча пройдена!")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Ошибка обработки капчи: {e}")
            return False
    
    @staticmethod
    async def random_mouse_movement(page: Page):
        """
        Случайные движения мыши.
        """
        try:
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.2, 0.8))
        except:
            pass
    
    @staticmethod
    async def handle_unexpected_modals(page: Page):
        """
        Закрывает неожиданные модальные окна (куки, уведомления).
        """
        try:
            # Модалка с куки
            cookie_accept = page.locator('[data-qa="cookie-accept"]')
            if await cookie_accept.count() > 0:
                await cookie_accept.click()
                await asyncio.sleep(0.5)
            
            # Модалка с уведомлением
            notif_close = page.locator('[data-qa="notification-close"]')
            if await notif_close.count() > 0:
                await notif_close.click()
                await asyncio.sleep(0.5)
        except:
            pass
