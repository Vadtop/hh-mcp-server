"""
Сервис откликов (через браузер).

Реализует:
- Отклик на вакансию (клик по кнопке)
- Обработка модальных окон (письмо, вопросы)
- История откликов
- Мониторинг статусов
"""

import logging
from typing import Optional

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.browser.parsers import NegotiationParser
from src.browser.actions import BrowserActions

logger = logging.getLogger(__name__)


class ApplyService:
    """
    Сервис откликов через Playwright.
    """

    def __init__(self, browser: BrowserEngine):
        self.browser = browser
        self.auth = HHAuth(browser)

    async def apply(
        self,
        vacancy_id: str,
        cover_letter: Optional[str] = None,
    ) -> dict:
        """
        Откликается на вакансию.

        Args:
            vacancy_id: ID вакансии
            cover_letter: Сопроводительное письмо

        Returns:
            dict с результатом отклика
        """
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}

        page_obj = await self.browser.new_page()
        actions = BrowserActions(page_obj)

        try:
            url = f"https://hh.ru/vacancy/{vacancy_id}"
            await actions.goto(url)

            # Сначала кликаем кнопку отклика
            result = await actions.click_apply_button()

            # Если отклик сразу прошёл (без письма) — пробуем добавить письмо
            if result.get("success") and cover_letter:
                # Отклик уже отправлен без письма — на hh.ru можно добавить письмо
                # в переписке. Открываем страницу отклика
                logger.info(
                    f"Отклик отправлен, добавляем письмо к вакансии {vacancy_id}"
                )
                letter_page = await self.browser.new_page()
                try:
                    await letter_page.goto(
                        f"https://hh.ru/applicant/negotiations/vacancy/{vacancy_id}",
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    await letter_page.wait_for_timeout(2000)

                    # Ищем кнопку "Написать" / "Прикрепить письмо"
                    write_selectors = [
                        'a:has-text("Написать")',
                        'button:has-text("Написать")',
                        'a:has-text("Написать письмо")',
                        '[data-qa*="write-message"]',
                        '[data-qa*="add-letter"]',
                    ]
                    for sel in write_selectors:
                        loc = letter_page.locator(sel)
                        if await loc.count() > 0:
                            await loc.first.click()
                            await letter_page.wait_for_timeout(1000)

                            # Ищем textarea для письма
                            textarea = letter_page.locator("textarea").first
                            if await textarea.count() > 0:
                                await textarea.fill(cover_letter)
                                await letter_page.wait_for_timeout(500)

                                # Кнопка отправки
                                send_btn = letter_page.locator(
                                    'button:has-text("Отправить"), '
                                    'button:has-text("Написать"), '
                                    '[data-qa*="send"], '
                                    '[data-qa*="submit"]'
                                ).first
                                if await send_btn.count() > 0:
                                    await send_btn.click()
                                    await letter_page.wait_for_timeout(2000)
                                    logger.info("Письмо добавлено к отклику")

                            break
                except Exception as e:
                    logger.warning(f"Не удалось добавить письмо: {e}")
                finally:
                    await letter_page.close()

                return {
                    "success": True,
                    "message": "Отклик отправлен"
                    + (" с письмом" if cover_letter else ""),
                    "vacancy_id": vacancy_id,
                }

            if result.get("success"):
                return {
                    "success": True,
                    "message": "Отклик отправлен!",
                    "vacancy_id": vacancy_id,
                }

            elif result.get("needs_letter") and cover_letter:
                letter_success = await actions.fill_cover_letter(cover_letter)
                if letter_success:
                    return {
                        "success": True,
                        "message": "Отклик с письмом отправлен!",
                        "vacancy_id": vacancy_id,
                    }
                else:
                    return {"error": "Не удалось отправить письмо"}

            elif result.get("needs_letter") and not cover_letter:
                return {
                    "error": "Вакансия требует сопроводительное письмо",
                    "needs_letter": True,
                }

            elif result.get("has_questions"):
                return {
                    "error": "Вакансия имеет вопросы — требуется ручное заполнение",
                    "has_questions": True,
                }

            else:
                return {"error": result.get("error", "Неизвестная ошибка")}

        except Exception as e:
            logger.error(f"Ошибка отклика: {e}")
            return {"error": str(e)}
        finally:
            await page_obj.close()

    async def get_applications(self) -> list[dict]:
        """
        Получает историю откликов.

        Returns:
            Список откликов
        """
        if not await self.auth.ensure_authenticated():
            return []

        page_obj = await self.browser.new_page()

        try:
            return await NegotiationParser.parse_applications(page_obj)
        except Exception as e:
            logger.error(f"Ошибка получения откликов: {e}")
            return []
        finally:
            await page_obj.close()

    async def check_application_status(self, vacancy_id: str) -> dict:
        """
        Проверяет статус конкретного отклика.

        Args:
            vacancy_id: ID вакансии

        Returns:
            dict со статусом
        """
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}

        page_obj = await self.browser.new_page()

        try:
            url = f"https://hh.ru/applicant/negotiations/vacancy/{vacancy_id}"
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

            return await NegotiationParser.parse_application_status(page_obj)
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {e}")
            return {"error": str(e)}
        finally:
            await page_obj.close()
