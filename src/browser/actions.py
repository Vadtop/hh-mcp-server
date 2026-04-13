"""
Действия в браузере.

Реализует:
- Навигация по hh.ru
- Клик по кнопкам (отклик, пагинация)
- Скролл страницы
- Заполнение форм
- Обработка модальных окон
"""

import random
import asyncio
import logging
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.browser.anti_detect import AntiDetect

logger = logging.getLogger(__name__)


class BrowserActions:
    """
    Действия в браузере с анти-детект мерами.
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.anti_detect = AntiDetect()
    
    async def goto(self, url: str, wait_until: str = "networkidle"):
        """
        Переход на URL с анти-детект задержкой.
        """
        await self.anti_detect.random_delay()
        await self.page.goto(url, wait_until=wait_until, timeout=30000)
        await self.anti_detect.random_delay()
    
    async def scroll_to_bottom(self):
        """
        Плавно скроллит страницу до конца.
        """
        await self.page.evaluate("""
            async () => {
                const distance = document.body.scrollHeight - window.innerHeight;
                const steps = 10;
                const step = distance / steps;
                
                for (let i = 0; i < steps; i++) {
                    window.scrollBy(0, step);
                    await new Promise(r => setTimeout(r, 100 + Math.random() * 200));
                }
            }
        """)
        await self.anti_detect.random_delay()
    
    async def click_vacancy(self, vacancy_index: int = 0) -> bool:
        """
        Кликает на вакансию в результатах поиска.
        """
        try:
            vacancies = self.page.locator('[data-qa="search-result-item"]')
            await vacancies.nth(vacancy_index).click()
            await self.anti_detect.random_delay()
            return True
        except Exception as e:
            logger.error(f"Ошибка клика по вакансии: {e}")
            return False
    
    async def click_apply_button(self, vacancy_index: int = 0) -> dict:
        """
        Кликает кнопку «Откликнуться» в карточке вакансии.

        Returns:
            dict с результатом:
            - success: bool
            - needs_letter: bool (требуется письмо)
            - has_questions: bool (есть вопросы)
            - error: str (ошибка)
        """
        try:
            # Кнопка отклика — несколько вариантов селектора
            apply_selectors = [
                '[data-qa="vacancy-response"]',
                '[data-qa="vacancy-response-link"]',
                'a[href*="applicant/vacancy_response"]',
                'button[data-qa*="response"]',
            ]
            apply_btn = None
            for sel in apply_selectors:
                loc = self.page.locator(sel).nth(vacancy_index)
                if await loc.count() > 0:
                    apply_btn = loc
                    break

            if apply_btn is None:
                return {"success": False, "error": "Кнопка отклика не найдена"}

            await apply_btn.click()
            await self.anti_detect.random_delay()

            # Ждём реакцию страницы
            await self.page.wait_for_timeout(2000)

            # 1. Модальное окно с письмом — несколько вариантов
            letter_selectors = [
                '[data-qa="cover-letter-modal"]',
                '[data-qa="vacancy-response-popup"]',
                'textarea[data-qa*="letter"]',
                'textarea[placeholder*="письм"]',
                'textarea[placeholder*="Напишите"]',
                '.vacancy-response-letter',
            ]
            for sel in letter_selectors:
                if await self.page.locator(sel).count() > 0:
                    return {"success": False, "needs_letter": True, "has_questions": False}

            # 2. Вопросы от работодателя
            question_selectors = [
                '[data-qa="vacancy-questions"]',
                '[data-qa="applicant-questions"]',
                '.vacancy-questions',
            ]
            for sel in question_selectors:
                if await self.page.locator(sel).count() > 0:
                    return {"success": False, "needs_letter": False, "has_questions": True}

            # 3. Snackbar / уведомление об успехе
            snackbar_selectors = [
                '[data-qa="snackbar"]',
                '[class*="notification"]',
                '[class*="toast"]',
            ]
            for sel in snackbar_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    text = await loc.inner_text()
                    if any(w in text.lower() for w in ["отклик", "отправ", "успешно"]):
                        return {"success": True, "needs_letter": False, "has_questions": False}

            # 4. Редирект на страницу отклика
            if any(w in self.page.url.lower() for w in ["response", "negotiations"]):
                return {"success": True, "needs_letter": False, "has_questions": False}

            return {"success": False, "error": "Неизвестный результат отклика"}

        except Exception as e:
            logger.error(f"Ошибка отклика: {e}")
            return {"success": False, "error": str(e)}
    
    async def fill_cover_letter(self, letter: str) -> bool:
        """
        Заполняет сопроводительное письмо в модальном окне.
        """
        try:
            # Поле для письма — несколько вариантов
            input_selectors = [
                '[data-qa="cover-letter-input"]',
                'textarea[data-qa*="letter"]',
                'textarea[placeholder*="письм"]',
                'textarea[placeholder*="Напишите"]',
                'textarea[placeholder*="сопроводительн"]',
                '.vacancy-response-letter textarea',
            ]
            letter_input = None
            for sel in input_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    letter_input = loc
                    break

            if letter_input is None:
                logger.error("Поле для письма не найдено")
                return False

            await letter_input.fill(letter)
            await self.anti_detect.random_delay()

            # Кнопка отправки — несколько вариантов
            submit_selectors = [
                '[data-qa="cover-letter-submit"]',
                '[data-qa="vacancy-response-submit"]',
                'button[type="submit"]',
                'button[data-qa*="submit"]',
                'button[data-qa*="response"]',
            ]
            submit_btn = None
            for sel in submit_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    submit_btn = loc
                    break

            if submit_btn is None:
                logger.error("Кнопка отправки не найдена")
                return False

            await submit_btn.click()
            await self.anti_detect.random_delay()

            # Ждём подтверждение (любой из вариантов)
            try:
                await self.page.wait_for_selector(
                    '[data-qa="snackbar"], [class*="notification"], [class*="toast"]',
                    timeout=10000
                )
            except Exception:
                # Если snackbar не появился — проверяем редирект
                if any(w in self.page.url.lower() for w in ["response", "negotiations"]):
                    return True

            return True
        except Exception as e:
            logger.error(f"Ошибка заполнения письма: {e}")
            return False
    
    async def search_vacancies(self, query: str, filters: dict = None) -> bool:
        """
        Выполняет поиск вакансий.
        """
        try:
            # Переходим на hh.ru
            await self.goto("https://hh.ru/search/vacancy")
            
            # Находим поле поиска
            search_input = self.page.locator('[data-qa="search-bar-input"]')
            await search_input.fill(query)
            await self.anti_detect.random_delay()
            
            # Нажимаем Enter или кнопку поиска
            await self.page.keyboard.press("Enter")
            await self.anti_detect.random_delay()
            
            # Ждём результаты
            await self.page.wait_for_selector('[data-qa="search-result-item"]', timeout=15000)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return False
    
    async def navigate_to_resumes(self) -> bool:
        """Переход на страницу резюме."""
        try:
            await self.goto("https://hh.ru/resume/mine")
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации к резюме: {e}")
            return False
    
    async def navigate_to_applications(self) -> bool:
        """Переход на страницу откликов."""
        try:
            await self.goto("https://hh.ru/applicant/negotiations")
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации к откликам: {e}")
            return False
    
    async def close_modal(self) -> bool:
        """Закрывает модальное окно."""
        try:
            close_btn = self.page.locator('[data-qa="modal-close"]')
            if await close_btn.count() > 0:
                await close_btn.click()
                await self.anti_detect.random_delay()
                return True
            return False
        except:
            return False
    
    async def go_back(self) -> bool:
        """Возврат на предыдущую страницу."""
        try:
            await self.page.go_back()
            await self.anti_detect.random_delay()
            return True
        except:
            return False
    
    async def go_forward(self) -> bool:
        """Переход вперёд."""
        try:
            await self.page.go_forward()
            await self.anti_detect.random_delay()
            return True
        except:
            return False
