"""
Парсеры страниц hh.ru.

Извлекает структурированные данные из HTML:
- Список вакансий из поиска
- Детали вакансии
- Информация о работодателе
- Список резюме
- Статус откликов
"""

import re
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class VacancyParser:
    """Парсер вакансий."""

    @staticmethod
    async def parse_search_results(page: Page) -> list[dict]:
        """
        Парсит страницу поиска вакансий.
        """
        vacancies = []

        try:
            await page.wait_for_timeout(2000)

            # Актуальные селекторы hh.ru 2025-2026
            card_selectors = [
                '[data-qa="vacancy-serp__vacancy"]',
                '[data-qa="search-result-item"]',
            ]

            cards = []
            for sel in card_selectors:
                loc = page.locator(sel)
                count = await loc.count()
                if count > 0:
                    cards = await loc.all()
                    logger.info(f"Найдено {count} карточек по селектору: {sel}")
                    break

            if not cards:
                logger.warning("Стандартные селекторы не найдены, пробую альтернативы")
                return await VacancyParser._parse_alternative_results(page)

            for card in cards:
                try:
                    vacancy = await VacancyParser._parse_vacancy_card(card)
                    if vacancy:
                        vacancies.append(vacancy)
                except Exception as e:
                    logger.warning(f"Ошибка парсинга карточки: {e}")

            logger.info(f"Найдено {len(vacancies)} вакансий на странице")
            return vacancies

        except Exception as e:
            logger.error(f"Ошибка парсинга результатов: {e}")
            return await VacancyParser._parse_alternative_results(page)

    @staticmethod
    async def _parse_alternative_results(page: Page) -> list[dict]:
        """Альтернативный парсинг через ссылки на вакансии."""
        vacancies = []

        try:
            links = page.locator('[data-qa="serp-item__title"]')
            count = await links.count()

            for i in range(min(count, 20)):
                try:
                    link = links.nth(i)
                    title = await link.inner_text()
                    href = await link.get_attribute("href")

                    if title and href and "/vacancy/" in href:
                        match = re.search(r"/vacancy/(\d+)", href)
                        vacancy_id = match.group(1) if match else ""

                        vacancies.append(
                            {
                                "id": vacancy_id,
                                "title": title.strip()[:100],
                                "url": f"https://hh.ru{href}"
                                if href.startswith("/")
                                else href,
                            }
                        )
                except Exception:
                    continue

            logger.info(f"Альтернативный парсинг: {len(vacancies)} вакансий")
            return vacancies
        except Exception as e:
            logger.error(f"Альтернативный парсинг не удался: {e}")
            return []

    @staticmethod
    async def _parse_vacancy_card(card) -> Optional[dict]:
        """Парсит отдельную карточку вакансии (serp)."""
        try:
            # Название вакансии
            title_el = card.locator('[data-qa="serp-item__title"]')
            title = await title_el.inner_text() if await title_el.count() > 0 else ""

            # Ссылка на вакансию
            link_el = card.locator('[data-qa="serp-item__title"]')
            url = (
                await link_el.get_attribute("href") if await link_el.count() > 0 else ""
            )

            # Извлекаем ID из URL
            vacancy_id = ""
            if url:
                match = re.search(r"/vacancy/(\d+)", url)
                if match:
                    vacancy_id = match.group(1)

            # Компания
            company_el = card.locator('[data-qa="vacancy-serp__vacancy-employer"]')
            company = (
                await company_el.inner_text() if await company_el.count() > 0 else ""
            )

            # Зарплата
            salary_el = card.locator(
                '[data-qa="vacancy-serp__compensation"], [class*="compensation"]'
            )
            salary = (
                await salary_el.first.inner_text()
                if await salary_el.count() > 0
                else ""
            )

            # Локация
            location_el = card.locator('[data-qa="vacancy-serp__vacancy-address"]')
            location = (
                await location_el.inner_text() if await location_el.count() > 0 else ""
            )

            # Описание/сниппет
            desc_el = card.locator('[data-qa="vacancy-serp__vacancySnippet"]')
            description = (
                await desc_el.inner_text() if await desc_el.count() > 0 else ""
            )

            # Опыт работы
            experience_els = card.locator(
                '[data-qa*="vacancy-serp__vacancy-work-experience-"]'
            )
            experience = ""
            if await experience_els.count() > 0:
                experience = await experience_els.first.inner_text()

            # Удалёнка
            remote_el = card.locator('[data-qa="vacancy-label-work-schedule-remote"]')
            is_remote = await remote_el.count() > 0

            # Кнопка отклика
            has_apply = (
                await card.locator('[data-qa="vacancy-serp__vacancy_response"]').count()
                > 0
            )

            return {
                "id": vacancy_id,
                "title": title.strip(),
                "company": company.strip(),
                "salary": salary.strip(),
                "location": location.strip(),
                "description": description.strip(),
                "experience": experience.strip(),
                "remote": is_remote,
                "url": f"https://hh.ru{url}"
                if url and url.startswith("/")
                else (url or ""),
                "has_apply_button": has_apply,
            }

        except Exception as e:
            logger.warning(f"Ошибка парсинга карточки: {e}")
            return None

    @staticmethod
    async def _parse_pagination(page: Page) -> dict:
        """Парсит пагинацию."""
        try:
            # Текущая страница
            current_page_el = page.locator('[data-qa="pagination-page-active"]')
            current_page = (
                int(await current_page_el.inner_text())
                if await current_page_el.count() > 0
                else 1
            )

            # Всего страниц
            pages_el = page.locator('[data-qa="pagination-page"]')
            total_pages = await pages_el.count()

            return {
                "current_page": current_page,
                "total_pages": total_pages,
            }
        except Exception:
            return {"current_page": 1, "total_pages": 1}

    @staticmethod
    async def parse_vacancy_detail(page: Page) -> Optional[dict]:
        """
        Парсит детальную страницу вакансии.
        """
        try:
            await page.wait_for_timeout(2000)

            # Название
            title_el = page.locator('[data-qa="vacancy-title"]')
            title = await title_el.inner_text() if await title_el.count() > 0 else ""

            # Компания
            company_el = page.locator('[data-qa="vacancy-company-name"]')
            company = (
                await company_el.inner_text() if await company_el.count() > 0 else ""
            )

            # Зарплата
            salary_el = page.locator('[data-qa="vacancy-salary"]')
            salary = await salary_el.inner_text() if await salary_el.count() > 0 else ""

            # Опыт
            experience_el = page.locator('[data-qa="vacancy-experience"]')
            experience = (
                await experience_el.inner_text()
                if await experience_el.count() > 0
                else ""
            )

            # Тип занятости
            employment_el = page.locator('[data-qa="common-employment-text"]')
            employment = (
                await employment_el.inner_text()
                if await employment_el.count() > 0
                else ""
            )

            # Формат работы (удалёнка и т.д.)
            schedule_el = page.locator('[data-qa="work-formats-text"]')
            schedule = (
                await schedule_el.inner_text() if await schedule_el.count() > 0 else ""
            )

            # Локация
            location_el = page.locator('[data-qa="vacancy-area"]')
            location = (
                await location_el.inner_text() if await location_el.count() > 0 else ""
            )

            # Описание (HTML)
            desc_el = page.locator('[data-qa="vacancy-description"]')
            description = (
                await desc_el.inner_html() if await desc_el.count() > 0 else ""
            )

            # Ключевые навыки
            skills_els = page.locator('[data-qa="skills-element"]')
            skills = []
            for i in range(await skills_els.count()):
                skill = await skills_els.nth(i).inner_text()
                skills.append(skill.strip())

            # URL
            url = page.url

            # Извлекаем ID
            match = re.search(r"/vacancy/(\d+)", url)
            vacancy_id = match.group(1) if match else ""

            return {
                "id": vacancy_id,
                "title": title.strip(),
                "company": company.strip(),
                "salary": salary.strip(),
                "experience": experience.strip(),
                "employment": employment.strip(),
                "schedule": schedule.strip(),
                "location": location.strip(),
                "description": description,
                "skills": skills,
                "url": url,
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга деталей вакансии: {e}")
            return None


class ResumeParser:
    """Парсер резюме."""

    @staticmethod
    async def parse_resumes_list(page: Page) -> list[dict]:
        """
        Парсит список резюме пользователя.
        """
        resumes = []

        try:
            await page.goto(
                "https://hh.ru/applicant/resumes",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await page.wait_for_timeout(2000)

            # Ищем ссылки на резюме (data-qa="resume-card-link-XXXX")
            resume_links = page.locator('[data-qa^="resume-card-link"]')
            count = await resume_links.count()

            for i in range(count):
                item = resume_links.nth(i)

                try:
                    href = await item.get_attribute("href") or ""

                    # ID из href или data-qa
                    match = re.search(r"/resume/([a-f0-9]+)", href)
                    if not match:
                        qa = await item.get_attribute("data-qa") or ""
                        match = re.search(r"resume-card-link-([a-f0-9]+)", qa)
                    resume_id = match.group(1) if match else ""

                    # Название должности внутри карточки
                    title_el = item.locator('[data-qa="resume-title"]')
                    title = (
                        await title_el.inner_text()
                        if await title_el.count() > 0
                        else ""
                    )

                    # Статус
                    status_el = item.locator('[data-qa="resume-status"]')
                    status = (
                        await status_el.inner_text()
                        if await status_el.count() > 0
                        else ""
                    )

                    resumes.append(
                        {
                            "id": resume_id,
                            "title": title.strip(),
                            "url": f"https://hh.ru{href}"
                            if href.startswith("/")
                            else f"https://hh.ru/resume/{resume_id}",
                            "status": status.strip(),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Ошибка парсинга резюме: {e}")

            logger.info(f"Найдено {len(resumes)} резюме")
            return resumes

        except Exception as e:
            logger.error(f"Ошибка парсинга списка резюме: {e}")
            return []

    @staticmethod
    async def parse_resume_detail(page: Page) -> Optional[dict]:
        """Парсит детальную страницу резюме."""
        try:
            # Название должности
            title_el = page.locator('[data-qa="resume-title"]')
            title = await title_el.inner_text() if await title_el.count() > 0 else ""

            # Имя
            name_el = page.locator('[data-qa="resume-name"]')
            name = await name_el.inner_text() if await name_el.count() > 0 else ""

            # Возраст
            age_el = page.locator('[data-qa="resume-age"]')
            age_text = await age_el.inner_text() if await age_el.count() > 0 else ""

            # Зарплата
            salary_el = page.locator('[data-qa="resume-salary"]')
            salary = await salary_el.inner_text() if await salary_el.count() > 0 else ""

            # Навыки
            skills_els = page.locator('[data-qa="resume-skills"] li')
            skills = []
            for i in range(await skills_els.count()):
                skill = await skills_els.nth(i).inner_text()
                skills.append(skill.strip())

            # Опыт работы
            experience_els = page.locator('[data-qa="resume-experience"]')
            experience = []
            for i in range(await experience_els.count()):
                exp_text = await experience_els.nth(i).inner_text()
                experience.append(exp_text.strip())

            return {
                "title": title.strip(),
                "name": name.strip(),
                "age": age_text.strip(),
                "salary": salary.strip(),
                "skills": skills,
                "experience": experience,
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга резюме: {e}")
            return None


class NegotiationParser:
    """Парсер откликов/переговоров."""

    @staticmethod
    async def parse_applications(page: Page) -> list[dict]:
        """
        Парсит страницу «Мои отклики».

        Returns:
            Список откликов
        """
        applications = []

        try:
            await page.goto(
                "https://hh.ru/applicant/negotiations",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Находим все отклики
            items = page.locator('[data-qa="negotiation-item"]')
            count = await items.count()

            for i in range(count):
                item = items.nth(i)

                try:
                    # Название вакансии
                    title_el = item.locator('[data-qa="negotiation-vacancy"]')
                    title = (
                        await title_el.inner_text()
                        if await title_el.count() > 0
                        else ""
                    )

                    # Ссылка
                    link_el = item.locator('[data-qa="negotiation-vacancy"] a')
                    url = (
                        await link_el.get_attribute("href")
                        if await link_el.count() > 0
                        else ""
                    )

                    # ID вакансии
                    match = re.search(r"/vacancy/(\d+)", url) if url else None
                    vacancy_id = match.group(1) if match else ""

                    # Компания
                    company_el = item.locator('[data-qa="negotiation-employer"]')
                    company = (
                        await company_el.inner_text()
                        if await company_el.count() > 0
                        else ""
                    )

                    # Статус
                    status_el = item.locator('[data-qa="negotiation-status"]')
                    status = (
                        await status_el.inner_text()
                        if await status_el.count() > 0
                        else ""
                    )

                    # Дата отклика
                    date_el = item.locator('[data-qa="negotiation-date"]')
                    date = (
                        await date_el.inner_text() if await date_el.count() > 0 else ""
                    )

                    applications.append(
                        {
                            "vacancy_id": vacancy_id,
                            "title": title.strip(),
                            "company": company.strip(),
                            "status": status.strip(),
                            "date": date.strip(),
                            "url": f"https://hh.ru{url}" if url else "",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Ошибка парсинга отклика: {e}")

            logger.info(f"Найдено {len(applications)} откликов")
            return applications

        except Exception as e:
            logger.error(f"Ошибка парсинга откликов: {e}")
            return []

    @staticmethod
    async def parse_application_status(page: Page) -> dict:
        """
        Парсит статус конкретного отклика.

        Returns:
            dict со статусом
        """
        try:
            # Статус
            status_el = page.locator('[data-qa="negotiation-status"]')
            status = await status_el.inner_text() if await status_el.count() > 0 else ""

            # Есть ли ответ от работодателя
            has_response = (
                await page.locator('[data-qa="employer-response"]').count() > 0
            )

            # Приглашение?
            is_invited = "приглашен" in status.lower()
            is_refused = "отказ" in status.lower()

            return {
                "status": status.strip(),
                "has_response": has_response,
                "is_invited": is_invited,
                "is_refused": is_refused,
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга статуса: {e}")
            return {}
