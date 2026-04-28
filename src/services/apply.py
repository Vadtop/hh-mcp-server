"""
Сервис откликов (через браузер).

Реализует:
- Отклик на вакансию (клик по кнопке)
- Обработка модальных окон (письмо, вопросы)
- История откликов
- Мониторинг статусов
"""

import logging
import re

from src.browser.actions import BrowserActions
from src.browser.auth import HHAuth
from src.browser.engine import BrowserEngine
from src.browser.parsers import NegotiationParser
from src.browser.safe_page import safe_page
from src.services.applied_db import check_daily_limit, is_applied, mark_applied

logger = logging.getLogger(__name__)


def _validate_vacancy_id(vid: str) -> str:
    if not re.match(r"^\d{6,12}$", vid or ""):
        raise ValueError(f"Невалидный vacancy_id: {vid!r}")
    return vid


class ApplyService:
    """
    Сервис откликов через Playwright.
    """

    def __init__(self, browser: BrowserEngine, auth: HHAuth):
        self.browser = browser
        self.auth = auth

    async def apply(
        self,
        vacancy_id: str,
        cover_letter: str | None = None,
    ) -> dict:
        """
        Откликается на вакансию.

        A.3: Правильная логика:
        1. Идём на страницу вакансии.
        2. Если есть форма с textarea для письма — заполняем и сабмитим.
        3. Если формы нет — кликаем кнопку отклика без письма.
        4. Возвращаем letter_attached: bool.
        """
        try:
            _validate_vacancy_id(vacancy_id)
        except ValueError as e:
            return {"error": str(e)}

        if is_applied(vacancy_id):
            return {"error": "already_applied", "message": "Вы уже откликались на эту вакансию"}

        if not check_daily_limit():
            return {"error": "daily_limit_reached", "message": "Дневной лимит откликов исчерпан"}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            actions = BrowserActions(page_obj)

            try:
                url = f"https://hh.ru/vacancy/{vacancy_id}"
                await actions.goto(url)

                # A.3: Сначала проверяем, есть ли форма для письма ДО отклика
                letter_textarea = page_obj.locator(
                    'textarea[data-qa="vacancy-cover-letter-textarea"], '
                    'textarea[name="cover_letter"], '
                    'textarea.bloko-textarea'
                )

                if await letter_textarea.count() > 0 and cover_letter:
                    # Форма есть — заполняем письмо и сабмитим
                    await letter_textarea.first.fill(cover_letter)
                    await page_obj.wait_for_timeout(500)

                    # Кликаем кнопку отклика (она же отправит форму с письмом)
                    result = await actions.click_apply_button()

                    if result.get("success"):
                        mark_applied(vacancy_id, letter=cover_letter is not None)
                        return {
                            "success": True,
                            "message": "Отклик с письмом отправлен",
                            "vacancy_id": vacancy_id,
                            "letter_attached": True,
                        }
                    elif result.get("needs_letter"):
                        return {"error": "Не удалось отправить письмо через формы"}
                    else:
                        return {"error": result.get("error", "Не удалось откликнуться")}

                # Формы для письма нет — кликаем отклик сразу
                result = await actions.click_apply_button()

                if result.get("success"):
                    mark_applied(vacancy_id, letter=False)
                    return {
                        "success": True,
                        "message": "Отклик отправлен (без письма)",
                        "vacancy_id": vacancy_id,
                        "letter_attached": False,
                    }

                elif result.get("needs_letter") and cover_letter:
                    # После клика появилась форма — заполняем
                    letter_success = await actions.fill_cover_letter(cover_letter)
                    if letter_success:
                        return {
                            "success": True,
                            "message": "Отклик с письмом отправлен",
                            "vacancy_id": vacancy_id,
                            "letter_attached": True,
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

    async def get_applications(self) -> list[dict]:
        """
        Получает историю откликов.
        """
        if not await self.auth.ensure_authenticated():
            return []

        async with safe_page(self.browser) as page_obj:
            try:
                return await NegotiationParser.parse_applications(page_obj)
            except Exception as e:
                logger.error(f"Ошибка получения откликов: {e}")
                return []

    async def check_application_status(self, vacancy_id: str) -> dict:
        """
        Проверяет статус конкретного отклика.
        """
        try:
            _validate_vacancy_id(vacancy_id)
        except ValueError as e:
            return {"error": str(e)}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            try:
                url = f"https://hh.ru/applicant/negotiations/vacancy/{vacancy_id}"
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                return await NegotiationParser.parse_application_status(page_obj)
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
                return {"error": str(e)}
