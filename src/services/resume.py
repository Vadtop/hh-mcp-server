"""
Сервис резюме (через браузер).

Реализует:
- Получение списка резюме
- Получение деталей резюме
- Обновление резюме
"""

import logging
from typing import Optional

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.browser.parsers import ResumeParser
from src.browser.actions import BrowserActions

logger = logging.getLogger(__name__)


class ResumeService:
    """
    Сервис резюме через Playwright.
    """

    def __init__(self, browser: BrowserEngine):
        self.browser = browser
        self.auth = HHAuth(browser)

    async def get_my_resumes(self) -> list[dict]:
        """Получает список своих резюме."""
        if not await self.auth.ensure_authenticated():
            return []

        page_obj = await self.browser.new_page()

        try:
            return await ResumeParser.parse_resumes_list(page_obj)
        except Exception as e:
            logger.error(f"Ошибка получения резюме: {e}")
            return []
        finally:
            await page_obj.close()

    async def get_resume(self, resume_id: str) -> dict:
        """Получает детали резюме."""
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}

        page_obj = await self.browser.new_page()

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
        finally:
            await page_obj.close()

    async def update_resume(
        self,
        resume_id: str,
        title: Optional[str] = None,
        salary: Optional[int] = None,
        about: Optional[str] = None,
    ) -> dict:
        """Обновляет резюме."""
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}

        page_obj = await self.browser.new_page()
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
        finally:
            await page_obj.close()
