"""
Сервис вакансий (через браузер).

Реализует:
- Поиск вакансий через парсинг hh.ru
- Получение деталей вакансии
- Похожие вакансии
- Информация о работодателе
"""

import logging
from typing import Optional

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.browser.parsers import VacancyParser
from src.browser.actions import BrowserActions

logger = logging.getLogger(__name__)


class VacancyService:
    """
    Сервис вакансий через Playwright.
    """
    
    def __init__(self, browser: BrowserEngine):
        self.browser = browser
        self.auth = HHAuth(browser)
    
    async def search(
        self,
        text: str,
        area: Optional[str] = None,
        salary: Optional[int] = None,
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
        
        page_obj = await self.browser.new_page()
        actions = BrowserActions(page_obj)
        
        try:
            # Формируем URL поиска
            url = f"https://hh.ru/search/vacancy?page={page}&per_page={per_page}&text={text}"
            if remote:
                url += "&schedule=remote"
            elif area:
                url += f"&area={area}"
            if salary:
                url += f"&salary={salary}"
            
            logger.info(f"Поиск: {url}")
            await actions.goto(url)
            
            # Парсим результаты
            vacancies = await VacancyParser.parse_search_results(page_obj)
            
            return {
                "vacancies": vacancies,
                "found": len(vacancies),
                "page": page,
                "query": text,
            }
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return {"error": str(e), "vacancies": []}
        finally:
            await page_obj.close()
    
    async def get_vacancy(self, vacancy_id: str) -> dict:
        """
        Получает детали вакансии.
        
        Args:
            vacancy_id: ID вакансии
            
        Returns:
            dict с деталями вакансии
        """
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}
        
        page_obj = await self.browser.new_page()
        
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
        finally:
            await page_obj.close()
    
    async def get_similar(self, vacancy_id: str) -> list[dict]:
        """
        Получает похожие вакансии.
        """
        if not await self.auth.ensure_authenticated():
            return []
        
        page_obj = await self.browser.new_page()
        
        try:
            url = f"https://hh.ru/vacancy/{vacancy_id}/similar"
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            return await VacancyParser.parse_search_results(page_obj)
        except Exception as e:
            logger.error(f"Ошибка получения похожих вакансий: {e}")
            return []
        finally:
            await page_obj.close()
    
    async def get_employer(self, employer_id: str) -> dict:
        """
        Получает информацию о работодателе.
        """
        if not await self.auth.ensure_authenticated():
            return {"error": "Не удалось авторизоваться"}
        
        page_obj = await self.browser.new_page()
        
        try:
            url = f"https://hh.ru/employer/{employer_id}"
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Парсим информацию о компании
            name_el = page_obj.locator('[data-qa="employer-name"]')
            name = await name_el.inner_text() if await name_el.count() > 0 else ""
            
            desc_el = page_obj.locator('[data-qa="employer-description"]')
            desc = await desc_el.inner_text() if await desc_el.count() > 0 else ""
            
            return {
                "id": employer_id,
                "name": name.strip(),
                "description": desc.strip(),
            }
        except Exception as e:
            logger.error(f"Ошибка получения компании: {e}")
            return {"error": str(e)}
        finally:
            await page_obj.close()
