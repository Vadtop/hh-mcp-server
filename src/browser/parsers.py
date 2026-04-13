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
            # Ждём загрузки результатов (3 селектора fallback)
            selectors = [
                '[data-qa="search-result-item"]',
                '.search-result-item',
                'article[data-qa="search-result-item"]',
            ]
            
            selector_found = False
            for sel in selectors:
                try:
                    await page.wait_for_selector(sel, timeout=5000)
                    selector_found = True
                    break
                except:
                    continue
            
            if not selector_found:
                # Пробуем распарсить что есть
                logger.warning("Не найден стандартный селектор, пробую альтернативы")
                return await VacancyParser._parse_alternative_results(page)
            
            # Находим все карточки вакансий
            cards = await page.locator('[data-qa="search-result-item"]').all()
            
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
            # Fallback — пробуем альтернативный парсинг
            return await VacancyParser._parse_alternative_results(page)
    
    @staticmethod
    async def _parse_alternative_results(page: Page) -> list[dict]:
        """Альтернативный парсинг через общие селекторы."""
        vacancies = []
        
        try:
            # Ищем все ссылки на вакансии
            links = page.locator('a[href*="/vacancy/"]')
            count = await links.count()
            
            for i in range(min(count, 20)):
                try:
                    link = links.nth(i)
                    title = await link.inner_text()
                    href = await link.get_attribute("href")
                    
                    if title and href and '/vacancy/' in href:
                        match = re.search(r'/vacancy/(\d+)', href)
                        vacancy_id = match.group(1) if match else ""
                        
                        vacancies.append({
                            "id": vacancy_id,
                            "title": title.strip()[:100],
                            "url": f"https://hh.ru{href}" if href.startswith("/") else href,
                        })
                except:
                    continue
            
            logger.info(f"Альтернативный парсинг: {len(vacancies)} вакансий")
            return vacancies
        except Exception as e:
            logger.error(f"Альтернативный парсинг не удался: {e}")
            return []
    
    @staticmethod
    async def _parse_vacancy_card(card) -> Optional[dict]:
        """Парсит отдельную карточку вакансии."""
        try:
            # Название вакансии
            title_el = card.locator('[data-qa="search-result-item-title"]')
            title = await title_el.inner_text() if await title_el.count() > 0 else ""
            
            # Ссылка на вакансию
            link_el = card.locator('[data-qa="search-result-item-title"] a')
            url = await link_el.get_attribute("href") if await link_el.count() > 0 else ""
            
            # Извлекаем ID из URL
            vacancy_id = ""
            if url:
                match = re.search(r'/vacancy/(\d+)', url)
                if match:
                    vacancy_id = match.group(1)
            
            # Компания
            company_el = card.locator('[data-qa="search-result-item-employer"]')
            company = await company_el.inner_text() if await company_el.count() > 0 else ""
            
            # Зарплата
            salary_el = card.locator('[data-qa="search-result-item-salary"]')
            salary = await salary_el.inner_text() if await salary_el.count() > 0 else ""
            
            # Локация
            location_el = card.locator('[data-qa="search-result-item-area"]')
            location = await location_el.inner_text() if await location_el.count() > 0 else ""
            
            # Описание/требования
            desc_el = card.locator('[data-qa="search-result-item-description"]')
            description = await desc_el.inner_text() if await desc_el.count() > 0 else ""
            
            # Дата публикации
            date_el = card.locator('[data-qa="search-result-item-publish-date"]')
            publish_date = await date_el.inner_text() if await date_el.count() > 0 else ""
            
            # Кнопка отклика (есть ли)
            has_apply = await card.locator('[data-qa="vacancy-response"]').count() > 0
            
            return {
                "id": vacancy_id,
                "title": title.strip(),
                "company": company.strip(),
                "salary": salary.strip(),
                "location": location.strip(),
                "description": description.strip(),
                "publish_date": publish_date.strip(),
                "url": f"https://hh.ru{url}" if url else "",
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
            current_page = int(await current_page_el.inner_text()) if await current_page_el.count() > 0 else 1
            
            # Всего страниц
            pages_el = page.locator('[data-qa="pagination-page"]')
            total_pages = await pages_el.count()
            
            return {
                "current_page": current_page,
                "total_pages": total_pages,
            }
        except:
            return {"current_page": 1, "total_pages": 1}
    
    @staticmethod
    async def parse_vacancy_detail(page: Page) -> Optional[dict]:
        """
        Парсит детальную страницу вакансии.
        
        Args:
            page: Страница вакансии
            
        Returns:
            dict с деталями вакансии
        """
        try:
            # Ждём загрузки
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Название
            title_el = page.locator('[data-qa="vacancy-title"]')
            title = await title_el.inner_text() if await title_el.count() > 0 else ""
            
            # Компания
            company_el = page.locator('[data-qa="vacancy-company"]')
            company = await company_el.inner_text() if await company_el.count() > 0 else ""
            
            # Зарплата
            salary_el = page.locator('[data-qa="vacancy-salary"]')
            salary = await salary_el.inner_text() if await salary_el.count() > 0 else ""
            
            # Опыт
            experience_el = page.locator('[data-qa="vacancy-experience"]')
            experience = await experience_el.inner_text() if await experience_el.count() > 0 else ""
            
            # Тип занятости
            employment_el = page.locator('[data-qa="vacancy-employment"]')
            employment = await employment_el.inner_text() if await employment_el.count() > 0 else ""
            
            # График работы
            schedule_el = page.locator('[data-qa="vacancy-schedule"]')
            schedule = await schedule_el.inner_text() if await schedule_el.count() > 0 else ""
            
            # Локация
            location_el = page.locator('[data-qa="vacancy-area"]')
            location = await location_el.inner_text() if await location_el.count() > 0 else ""
            
            # Описание (HTML)
            desc_el = page.locator('[data-qa="vacancy-description"]')
            description = await desc_el.inner_html() if await desc_el.count() > 0 else ""
            
            # Ключевые навыки
            skills_els = page.locator('[data-qa="vacancy-skills"] li')
            skills = []
            for i in range(await skills_els.count()):
                skill = await skills_els.nth(i).inner_text()
                skills.append(skill.strip())
            
            # URL
            url = page.url
            
            # Извлекаем ID
            match = re.search(r'/vacancy/(\d+)', url)
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
        
        Returns:
            Список резюме
        """
        resumes = []
        
        try:
            await page.goto("https://hh.ru/resume/mine", wait_until="networkidle", timeout=15000)
            
            # Находим все резюме
            resume_items = page.locator('[data-qa="resume-item"]')
            count = await resume_items.count()
            
            for i in range(count):
                item = resume_items.nth(i)
                
                try:
                    # Название должности
                    title_el = item.locator('[data-qa="resume-title"]')
                    title = await title_el.inner_text() if await title_el.count() > 0 else ""
                    
                    # Ссылка
                    link_el = item.locator('[data-qa="resume-title"] a')
                    url = await link_el.get_attribute("href") if await link_el.count() > 0 else ""
                    
                    # ID
                    match = re.search(r'/resume/([a-f0-9]+)', url) if url else None
                    resume_id = match.group(1) if match else ""
                    
                    # Статус
                    status_el = item.locator('[data-qa="resume-status"]')
                    status = await status_el.inner_text() if await status_el.count() > 0 else ""
                    
                    # Дата обновления
                    updated_el = item.locator('[data-qa="resume-update-date"]')
                    updated = await updated_el.inner_text() if await updated_el.count() > 0 else ""
                    
                    resumes.append({
                        "id": resume_id,
                        "title": title.strip(),
                        "url": f"https://hh.ru{url}" if url else "",
                        "status": status.strip(),
                        "updated": updated.strip(),
                    })
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
            await page.goto("https://hh.ru/applicant/negotiations", wait_until="networkidle", timeout=15000)
            
            # Находим все отклики
            items = page.locator('[data-qa="negotiation-item"]')
            count = await items.count()
            
            for i in range(count):
                item = items.nth(i)
                
                try:
                    # Название вакансии
                    title_el = item.locator('[data-qa="negotiation-vacancy"]')
                    title = await title_el.inner_text() if await title_el.count() > 0 else ""
                    
                    # Ссылка
                    link_el = item.locator('[data-qa="negotiation-vacancy"] a')
                    url = await link_el.get_attribute("href") if await link_el.count() > 0 else ""
                    
                    # ID вакансии
                    match = re.search(r'/vacancy/(\d+)', url) if url else None
                    vacancy_id = match.group(1) if match else ""
                    
                    # Компания
                    company_el = item.locator('[data-qa="negotiation-employer"]')
                    company = await company_el.inner_text() if await company_el.count() > 0 else ""
                    
                    # Статус
                    status_el = item.locator('[data-qa="negotiation-status"]')
                    status = await status_el.inner_text() if await status_el.count() > 0 else ""
                    
                    # Дата отклика
                    date_el = item.locator('[data-qa="negotiation-date"]')
                    date = await date_el.inner_text() if await date_el.count() > 0 else ""
                    
                    applications.append({
                        "vacancy_id": vacancy_id,
                        "title": title.strip(),
                        "company": company.strip(),
                        "status": status.strip(),
                        "date": date.strip(),
                        "url": f"https://hh.ru{url}" if url else "",
                    })
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
            has_response = await page.locator('[data-qa="employer-response"]').count() > 0
            
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
