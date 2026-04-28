"""
Сервис вакансий (через браузер).

Реализует:
- Поиск вакансий через парсинг hh.ru
- Получение деталей вакансии
- Похожие вакансии
- Информация о работодателе
"""

import logging
import re
from urllib.parse import quote

from src.browser.actions import BrowserActions
from src.browser.auth import HHAuth
from src.browser.engine import BrowserEngine
from src.browser.parsers import VacancyParser
from src.browser.safe_page import safe_page

logger = logging.getLogger(__name__)


def _validate_vacancy_id(vid: str) -> str:
    if not re.match(r"^\d{6,12}$", vid or ""):
        raise ValueError(f"Невалидный vacancy_id: {vid!r}")
    return vid


def _validate_employer_id(eid: str) -> str:
    if not re.match(r"^\d{4,12}$", eid or ""):
        raise ValueError(f"Невалидный employer_id: {eid!r}")
    return eid


class VacancyService:
    """
    Сервис вакансий через Playwright.
    """

    def __init__(self, browser: BrowserEngine, auth: HHAuth):
        self.browser = browser
        self.auth = auth
        self._page = None

    async def search(
        self,
        text: str,
        area: str | None = None,
        salary: int | None = None,
        remote: bool = False,
        page: int = 0,
        per_page: int = 20,
    ) -> dict:
        """
        Ищет вакансии через парсинг hh.ru.

        Args:
            text: Поисковый запрос
            area: Регион (ID)
            salary: Минимальная зарплата
            page: Номер страницы
            per_page: Количество на странице

        Returns:
            dict с вакансиями и пагинацией
        """
        # Авторизуемся
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}

        # Переиспользуем одну страницу для всех поисков (быстрее)
        if self._page is None or self._page.is_closed():
            self._page = await self.browser.new_page()
        actions = BrowserActions(self._page)

        try:
            # Формируем URL поиска
            url = f"https://hh.ru/search/vacancy?page={page}&per_page={per_page}&text={quote(text)}"
            if remote:
                url += "&schedule=remote"
            elif area:
                url += f"&area={area}"
            if salary:
                url += f"&salary={salary}"

            logger.info(f"Поиск: {url}")
            await actions.goto(url)

            # Парсим результаты
            vacancies = await VacancyParser.parse_search_results(self._page)

            return {
                "vacancies": vacancies,
                "found": len(vacancies),
                "page": page,
                "query": text,
            }

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            self._page = None  # сбрасываем страницу при ошибке
            return {"error": str(e), "vacancies": []}

    async def get_vacancy(self, vacancy_id: str) -> dict:
        """
        Получает детали вакансии.
        """
        try:
            _validate_vacancy_id(vacancy_id)
        except ValueError as e:
            return {"error": str(e)}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            try:
                url = f"https://hh.ru/vacancy/{vacancy_id}"
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                vacancy = await VacancyParser.parse_vacancy_detail(page_obj)

                if vacancy:
                    return vacancy
                else:
                    return {"error": "Не удалось распарсить вакансию"}

            except Exception as e:
                logger.error(f"Ошибка получения вакансии: {e}")
                return {"error": str(e)}

    async def get_similar(self, vacancy_id: str) -> list[dict]:
        """
        Получает похожие вакансии.
        """
        try:
            _validate_vacancy_id(vacancy_id)
        except ValueError:
            return []

        if not await self.auth.ensure_authenticated():
            return []

        async with safe_page(self.browser) as page_obj:
            try:
                url = f"https://hh.ru/vacancy/{vacancy_id}/similar"
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                return await VacancyParser.parse_search_results(page_obj)
            except Exception as e:
                logger.error(f"Ошибка получения похожих вакансий: {e}")
                return []

    async def get_employer(self, employer_id: str) -> dict:
        """
        Получает информацию о работодателе.
        """
        try:
            _validate_employer_id(employer_id)
        except ValueError as e:
            return {"error": str(e)}

        if not await self.auth.ensure_authenticated():
            return {"error": "Сессия hh.ru истекла. Запустите `python auth_once.py` для повторного входа."}

        async with safe_page(self.browser) as page_obj:
            try:
                url = f"https://hh.ru/employer/{employer_id}"
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                name_el = page_obj.locator(
                    '[data-qa="employer-name"], [data-qa="vacancy-company-name"]'
                )
                name = await name_el.inner_text() if await name_el.count() > 0 else ""

                desc_el = page_obj.locator(
                    '[data-qa="employer-description"], .employer-description, .company-description'
                )
                desc = await desc_el.inner_text() if await desc_el.count() > 0 else ""

                return {
                    "id": employer_id,
                    "name": name.strip(),
                    "description": desc.strip(),
                }
            except Exception as e:
                logger.error(f"Ошибка получения компании: {e}")
                return {"error": str(e)}
