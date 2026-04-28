"""
Сервис резюме (через браузер).

Реализует:
- Получение списка резюме
- Получение деталей резюме
- Обновление резюме
"""

import logging
import re

from src.browser.actions import BrowserActions
from src.browser.auth import HHAuth
from src.browser.engine import BrowserEngine
from src.browser.parsers import ResumeParser
from src.browser.safe_page import safe_page

logger = logging.getLogger(__name__)


def _validate_resume_id(rid: str) -> str:
    if not re.match(r"^[a-f0-9]{20,40}$", rid or ""):
        raise ValueError(f"Невалидный resume_id: {rid!r}")
    return rid


class ResumeService:
    """
    Сервис резюме через Playwright.
    """

    def __init__(self, browser: BrowserEngine, auth: HHAuth):
        self.browser = browser
        self.auth = auth

    async def get_my_resumes(self) -> list[dict]:
        """Получает список своих резюме."""
        if not await self.auth.ensure_authenticated():
            return []

        async with safe_page(self.browser) as page_obj:
            try:
                return await ResumeParser.parse_resumes_list(page_obj)
            except Exception as e:
                logger.error(f"Ошибка получения резюме: {e}")
                return []

    async def get_resume(self, resume_id: str) -> dict:
        """Получает детали резюме."""
        try:
            _validate_resume_id(resume_id)
        except ValueError as e:
            return {"error": str(e)}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            try:
                url = f"https://hh.ru/resume/{resume_id}"
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                resume = await ResumeParser.parse_resume_detail(page_obj)

                if resume:
                    return resume
                else:
                    return {"error": "Не удалось распарсить резюме"}
            except Exception as e:
                logger.error(f"Ошибка получения резюме: {e}")
                return {"error": str(e)}

    async def update_resume(
        self,
        resume_id: str,
        title: str | None = None,
        salary: int | None = None,
        about: str | None = None,
    ) -> dict:
        """Обновляет резюме."""
        try:
            _validate_resume_id(resume_id)
        except ValueError as e:
            return {"error": str(e)}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            actions = BrowserActions(page_obj)

            try:
                url = f"https://hh.ru/resume/{resume_id}/edit"
                await actions.goto(url)

                if title:
                    title_input = page_obj.locator('[data-qa="resume-title-input"]')
                    if await title_input.count() > 0:
                        await title_input.fill(title)
                        await actions.anti_detect.random_delay()

                if salary:
                    salary_input = page_obj.locator('[data-qa="resume-salary-input"]')
                    if await salary_input.count() > 0:
                        await salary_input.fill(str(salary))
                        await actions.anti_detect.random_delay()

                if about:
                    about_input = page_obj.locator('[data-qa="resume-about-input"]')
                    if await about_input.count() > 0:
                        await about_input.fill(about)
                        await actions.anti_detect.random_delay()

                save_btn = page_obj.locator('[data-qa="resume-save"]')
                if await save_btn.count() > 0:
                    await save_btn.click()
                    await actions.anti_detect.random_delay()
                    return {"success": True, "message": "Резюме обновлено"}

                return {"error": "Не найдены поля для обновления или кнопка сохранения"}

            except Exception as e:
                logger.error(f"Ошибка обновления резюме: {e}")
                return {"error": str(e)}
