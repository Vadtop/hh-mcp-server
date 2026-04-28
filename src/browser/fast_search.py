"""
Быстрый поиск вакансий через requests + BeautifulSoup.

Используется для первичного поиска без браузера (в 15-20 раз быстрее Playwright).
Playwright используется только для раскрытия деталей топ-вакансий.
"""

import re
import time
import logging
import asyncio
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://hh.ru/",
}


class FastVacancySearch:
    """
    Быстрый поиск вакансий без браузера.
    Возвращает базовые данные: title, company, salary, url, snippet описания.
    """

    def search(
        self,
        text: str,
        remote: bool = True,
        per_page: int = 20,
        page: int = 0,
        delay: float = 1.5,
    ) -> list[dict]:
        """
        Поиск вакансий через HTTP запрос.

        Args:
            text: Поисковый запрос
            remote: Только удалённая работа
            per_page: Количество вакансий
            page: Номер страницы
            delay: Задержка перед запросом (анти-бот)

        Returns:
            Список вакансий с базовыми полями
        """
        time.sleep(delay)

        url = f"https://hh.ru/search/vacancy?text={quote(text)}&per_page={per_page}&page={page}"
        if remote:
            url += "&schedule=remote"

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                logger.warning(f"HTTP {r.status_code} для '{text}'")
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            return self._parse_cards(soup)

        except Exception as e:
            logger.error(f"Ошибка поиска '{text}': {e}")
            return []

    def _parse_cards(self, soup: BeautifulSoup) -> list[dict]:
        """Парсит карточки вакансий со страницы поиска."""
        vacancies = []

        cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
        if not cards:
            cards = soup.select('[data-qa="search-result-item"]')

        for card in cards:
            try:
                v = self._parse_card(card)
                if v:
                    vacancies.append(v)
            except Exception as e:
                logger.warning(f"Ошибка парсинга карточки: {e}")

        return vacancies

    def _parse_card(self, card) -> Optional[dict]:
        """Парсит одну карточку."""
        # Название и ссылка
        title_el = card.select_one('[data-qa="serp-item__title"]')
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        url = title_el.get("href", "")
        if url.startswith("/"):
            url = f"https://hh.ru{url}"

        # ID вакансии
        match = re.search(r"/vacancy/(\d+)", url)
        vacancy_id = match.group(1) if match else ""

        # Компания
        company_el = card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
        company = company_el.get_text(strip=True) if company_el else ""

        # Зарплата
        salary_el = card.select_one('[data-qa="vacancy-serp__compensation"]')
        if not salary_el:
            salary_el = card.select_one('[class*="compensation"]')
        salary = salary_el.get_text(strip=True) if salary_el else ""

        # Локация
        location_el = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
        location = location_el.get_text(strip=True) if location_el else ""

        # Сниппет описания
        desc_el = card.select_one('[data-qa="vacancy-serp__vacancySnippet"]')
        description = desc_el.get_text(strip=True) if desc_el else ""

        # Опыт
        exp_el = card.select_one('[data-qa*="vacancy-serp__vacancy-work-experience"]')
        experience = exp_el.get_text(strip=True) if exp_el else ""

        return {
            "id": vacancy_id,
            "title": title,
            "company": company,
            "salary": salary,
            "location": location,
            "description": description,
            "experience": experience,
            "skills": [],  # заполняется при раскрытии деталей
            "url": url,
        }

    async def search_async(self, text: str, remote: bool = True, per_page: int = 20) -> list[dict]:
        """Async обёртка для использования в async контексте."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.search(text, remote, per_page))
