"""
HH.ru MCP Server v2 — Точка входа.

MCP сервер с 19 инструментами для работы с hh.ru через Playwright:
- Поиск вакансий (парсинг)
- Управление резюме
- Автоотклики
- AI-скоринг
- Карьерный советник
- Мониторинг ответов
"""

import asyncio
import logging

from fastmcp import FastMCP

from src.ai.career_advisor import CareerAdvisor
from src.ai.letter_gen import LetterGenerator
from src.ai.market_analyzer import MarketAnalyzer
from src.ai.scorer import AIVacancyScorer
from src.browser.auth import HHAuth
from src.browser.engine import BrowserEngine
from src.config import (
    AI_MODEL,
    APP_NAME,
    APP_VERSION,
    MY_EXPECTED_SALARY,
    OPENROUTER_API_KEY,
)
from src.services.apply import ApplyService
from src.services.monitor import MonitorService
from src.services.resume import ResumeService
from src.services.vacancy import VacancyService

# Логирование
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# MCP сервер
mcp = FastMCP(APP_NAME)

# Глобальные объекты
_browser: BrowserEngine | None = None
_browser_started: bool = False
_auth: HHAuth | None = None
_vacancy_service: VacancyService | None = None
_resume_service: ResumeService | None = None
_apply_service: ApplyService | None = None
_ai_scorer: AIVacancyScorer | None = None
_letter_gen: LetterGenerator | None = None
_market_analyzer: MarketAnalyzer | None = None
_career_advisor: CareerAdvisor | None = None
_monitor: MonitorService | None = None

# A.1: Lock для защиты от race condition при параллельных tool calls
_init_lock = asyncio.Lock()
# A.12: Semaphore для ограничения параллельных browser actions
_browser_semaphore = asyncio.Semaphore(5)


async def get_browser() -> BrowserEngine:
    global _browser, _browser_started

    # Если браузер уже стартовал — возвращаем без лока
    if _browser is not None and _browser_started:
        return _browser

    async with _init_lock:
        # Double-check после лока
        if _browser is not None and _browser_started:
            return _browser

        if _browser is None:
            _browser = BrowserEngine(headless=True, slow_mo=0)

        if not _browser_started:
            try:
                await asyncio.wait_for(_browser.start(), timeout=30.0)
                _browser_started = True
            except Exception:
                # Сброс при ошибке — следующий вызов попробует заново
                logger.error("Browser start() failed, resetting state")
                try:
                    await _browser.close()
                except Exception:
                    pass
                _browser = None
                _browser_started = False
                raise

    return _browser


async def get_auth() -> HHAuth:
    global _auth

    if _auth is not None:
        return _auth

    # Берём браузер ВНЕ лока — get_browser() сам.lockится
    browser = await get_browser()

    async with _init_lock:
        if _auth is None:
            _auth = HHAuth(browser)

    return _auth


async def get_vacancy_service() -> VacancyService:
    global _vacancy_service

    if _vacancy_service is not None:
        return _vacancy_service

    browser = await get_browser()
    auth = await get_auth()

    async with _init_lock:
        if _vacancy_service is None:
            _vacancy_service = VacancyService(browser, auth=auth)

    return _vacancy_service


async def get_resume_service() -> ResumeService:
    global _resume_service

    if _resume_service is not None:
        return _resume_service

    browser = await get_browser()
    auth = await get_auth()

    async with _init_lock:
        if _resume_service is None:
            _resume_service = ResumeService(browser, auth=auth)

    return _resume_service


async def get_apply_service() -> ApplyService:
    global _apply_service

    if _apply_service is not None:
        return _apply_service

    browser = await get_browser()
    auth = await get_auth()

    async with _init_lock:
        if _apply_service is None:
            _apply_service = ApplyService(browser, auth=auth)

    return _apply_service


def get_ai_scorer() -> AIVacancyScorer:
    global _ai_scorer
    if _ai_scorer is None:
        _ai_scorer = AIVacancyScorer()
    return _ai_scorer


def get_letter_gen() -> LetterGenerator:
    global _letter_gen
    if _letter_gen is None:
        _letter_gen = LetterGenerator(
            openrouter_api_key=OPENROUTER_API_KEY, model=AI_MODEL
        )
    return _letter_gen


def get_market_analyzer() -> MarketAnalyzer:
    global _market_analyzer
    if _market_analyzer is None:
        _market_analyzer = MarketAnalyzer()
    return _market_analyzer


def get_career_advisor() -> CareerAdvisor:
    global _career_advisor
    if _career_advisor is None:
        _career_advisor = CareerAdvisor()
    return _career_advisor


async def get_monitor(interval: int = 300) -> MonitorService:
    global _monitor

    if _monitor is not None:
        return _monitor

    apply_service = await get_apply_service()

    async with _init_lock:
        if _monitor is None:
            _monitor = MonitorService(apply_service=apply_service, interval=interval)

    return _monitor


# ============================================================================
# MCP TOOLS: Вакансии (1-6)
# ============================================================================


@mcp.tool()
async def hh_search(
    text: str,
    area: str | None = None,
    salary: int | None = None,
    remote: bool = False,
    page: int = 0,
    per_page: int = 20,
) -> str:
    """
    Поиск вакансий на hh.ru через браузер.

    Args:
        text: Текст поиска (должность, ключевые слова)
        area: ID региона (не нужен при remote=True)
        salary: Минимальная зарплата
        remote: True = только удалённая работа по всей России
        page: Номер страницы
        per_page: Количество на странице

    Returns:
        Результаты поиска
    """
    service = await get_vacancy_service()

    result = await service.search(
        text=text,
        area=area,
        salary=salary,
        remote=remote,
        page=page,
        per_page=per_page,
    )

    if "error" in result:
        return f"❌ Ошибка: {result['error']}"

    vacancies = result.get("vacancies", [])

    if not vacancies:
        return f"🔍 По запросу '{text}' ничего не найдено"

    lines = [
        f"🔍 Поиск: {text}",
        f"📊 Найдено: {len(vacancies)} вакансий",
        f"📄 Страница {result.get('page', 0) + 1}",
        "",
    ]

    for i, v in enumerate(vacancies, 1):
        lines.append(f"{i}. {v.get('title', '')}")
        if v.get("company"):
            lines.append(f"   🏢 {v['company']}")
        if v.get("salary"):
            lines.append(f"   💰 {v['salary']}")
        if v.get("location"):
            lines.append(f"   📍 {v['location']}")
        if v.get("url"):
            lines.append(f"   🔗 {v['url']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def hh_bulk_search(
    queries: str,
    per_query: int = 10,
) -> str:
    """
    Поиск по нескольким запросам последовательно. Удалённо, вся Россия.

    Args:
        queries: Запросы через запятую, например: "AI разработчик, AI интегратор, LLM engineer"
        per_query: Количество вакансий на каждый запрос (по умолчанию 10)

    Returns:
        Все найденные вакансии без дублей, отсортированные по запросу
    """
    service = await get_vacancy_service()
    query_list = [q.strip() for q in queries.split(",") if q.strip()]

    all_vacancies = []
    seen_urls = set()
    lines = []

    for query in query_list:
        result = await service.search(text=query, remote=True, per_page=per_query)
        if "error" in result:
            lines.append(f"⚠️ '{query}': {result['error']}")
            continue

        vacancies = result.get("vacancies", [])
        new = [v for v in vacancies if v.get("url") not in seen_urls]
        for v in new:
            seen_urls.add(v.get("url"))
        all_vacancies.extend(new)
        lines.append(f"✅ '{query}': {len(new)} новых (всего {len(vacancies)})")

    lines.append(f"\n📊 Итого уникальных вакансий: {len(all_vacancies)}\n")

    for i, v in enumerate(all_vacancies, 1):
        lines.append(f"{i}. {v.get('title', '')}")
        if v.get("company"):
            lines.append(f"   🏢 {v['company']}")
        if v.get("salary"):
            lines.append(f"   💰 {v['salary']}")
        if v.get("location"):
            lines.append(f"   📍 {v['location']}")
        if v.get("url"):
            lines.append(f"   🔗 {v['url']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def hh_job_hunt(
    queries: str = "AI разработчик, AI интегратор, LLM engineer, разработчик ИИ агентов, python AI автоматизация",
    min_score: int = 60,
    per_query: int = 15,
    auto_apply: bool = False,
) -> str:
    """
    Полный цикл поиска работы: быстрый поиск → скоринг → отклик.

    Этапы:
    1. Быстрый поиск через HTTP (requests) — без браузера, ~4с на запрос
    2. Скоринг по данным карточки (заголовок, зарплата, сниппет)
    3. Автоотклик с AI письмом на вакансии выше min_score (если auto_apply=True)

    Args:
        queries: Поисковые запросы через запятую
        min_score: Минимальный скор для отклика (0-100)
        per_query: Вакансий на каждый запрос
        auto_apply: True = автоматически откликнуться на подходящие

    Returns:
        Список вакансий с оценками и результаты откликов
    """
    from src.browser.fast_search import FastVacancySearch

    scorer = get_ai_scorer()
    fast_search = FastVacancySearch()
    query_list = [q.strip() for q in queries.split(",") if q.strip()]
    seen_urls = set()
    all_vacancies = []

    # 1. Быстрый поиск через requests (не браузер)
    for query in query_list:
        vacancies = await fast_search.search_async(text=query, remote=True, per_page=per_query)
        for v in vacancies:
            if v.get("url") not in seen_urls:
                seen_urls.add(v.get("url"))
                all_vacancies.append(v)

    if not all_vacancies:
        return "❌ Вакансий не найдено"

    # 2. Скоринг по базовым данным карточки (без раскрытия страниц)
    scored_list = []
    for v in all_vacancies:
        scored = scorer.score_vacancy(v, expected_salary=MY_EXPECTED_SALARY)
        scored_list.append((scored.score, v, scored))
    scored_list.sort(key=lambda x: x[0], reverse=True)

    # 3. Формируем отчёт
    lines = [f"🎯 Найдено {len(all_vacancies)} вакансий по {len(query_list)} запросам\n"]

    apply_service = None
    letter_gen = None
    if auto_apply:
        apply_service = await get_apply_service()
        letter_gen = get_letter_gen()

    applied_count = 0

    for score, v, _scored in scored_list:
        title = v.get("title", "—")
        company = v.get("company", "—")
        salary = v.get("salary", "не указана")
        url = v.get("url", "")
        vacancy_id = v.get("id") or url.split("/vacancy/")[-1].split("?")[0] if url else ""

        emoji = "🟢" if score >= min_score else "🔴"
        lines.append(f"{emoji} {score}/100 — {title}")
        lines.append(f"   🏢 {company} | 💰 {salary}")
        lines.append(f"   🔗 {url}")

        # 5. Автоотклик
        if auto_apply and score >= min_score and vacancy_id and apply_service:
            try:
                letter = await letter_gen.generate_letter(vacancy=v, resume=None)
                result = await apply_service.apply(vacancy_id, letter)
                if "error" not in result:
                    lines.append("   ✅ Отклик отправлен")
                    applied_count += 1
                else:
                    lines.append(f"   ⚠️ {result['error']}")
            except Exception as e:
                lines.append(f"   ⚠️ {e}")

        lines.append("")

    above_min = len([x for x in scored_list if x[0] >= min_score])
    lines.append(f"{'=' * 50}")
    lines.append(f"📊 Всего: {len(scored_list)} | 🟢 Выше {min_score} баллов: {above_min}")
    if auto_apply:
        lines.append(f"✅ Откликов отправлено: {applied_count}")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_vacancy(vacancy_id: str) -> str:
    """
    Получить детальную информацию о вакансии.

    Args:
        vacancy_id: ID вакансии

    Returns:
        Детали вакансии
    """
    service = await get_vacancy_service()
    vacancy = await service.get_vacancy(vacancy_id)

    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"

    lines = [
        f"📌 {vacancy.get('title', '')}",
        f"{'=' * 50}",
    ]

    if vacancy.get("company"):
        lines.append(f"🏢 {vacancy['company']}")
    if vacancy.get("salary"):
        lines.append(f"💰 {vacancy['salary']}")
    if vacancy.get("experience"):
        lines.append(f"💼 Опыт: {vacancy['experience']}")
    if vacancy.get("employment"):
        lines.append(f"📋 {vacancy['employment']}")
    if vacancy.get("location"):
        lines.append(f"📍 {vacancy['location']}")

    if vacancy.get("skills"):
        lines.append("")
        lines.append("🔧 Навыки:")
        for skill in vacancy["skills"][:10]:
            lines.append(f"   • {skill}")

    if vacancy.get("url"):
        lines.append("")
        lines.append(f"🔗 {vacancy['url']}")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_employer(employer_id: str) -> str:
    """
    Получить информацию о компании/работодателе.

    Args:
        employer_id: ID работодателя

    Returns:
        Информация о компании
    """
    service = await get_vacancy_service()
    employer = await service.get_employer(employer_id)

    if "error" in employer:
        return f"❌ Ошибка: {employer['error']}"

    lines = [
        f"🏢 {employer.get('name', 'Неизвестно')}",
        f"{'=' * 50}",
    ]

    if employer.get("description"):
        lines.append(employer["description"][:500])

    return "\n".join(lines)


@mcp.tool()
async def hh_get_similar(vacancy_id: str) -> str:
    """
    Найти похожие вакансии.

    Args:
        vacancy_id: ID вакансии

    Returns:
        Похожие вакансии
    """
    service = await get_vacancy_service()
    similar = await service.get_similar(vacancy_id)

    if not similar:
        return "Похожих вакансий не найдено"

    lines = [f"🔍 Похожие вакансии ({len(similar)}):", ""]

    for i, v in enumerate(similar[:5], 1):
        lines.append(f"{i}. {v.get('title', '')}")
        if v.get("company"):
            lines.append(f"   🏢 {v['company']}")
        if v.get("salary"):
            lines.append(f"   💰 {v['salary']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_areas() -> str:
    """Получить список регионов/городов."""
    return "📍 Используйте hh.ru/search/vacancy для выбора региона"


@mcp.tool()
async def hh_get_dictionaries() -> str:
    """Получить справочные данные."""
    return "📚 Справочники доступны на hh.ru"


# ============================================================================
# MCP TOOLS: Резюме (7-9)
# ============================================================================


@mcp.tool()
async def hh_get_my_resumes() -> str:
    """
    Получить список своих резюме.

    Returns:
        Список резюме
    """
    service = await get_resume_service()
    resumes = await service.get_my_resumes()

    if not resumes:
        return "Резюме не найдены"

    lines = [f"📄 Мои резюме ({len(resumes)}):", ""]

    for r in resumes:
        lines.append(f"• {r.get('title', '')}")
        if r.get("status"):
            lines.append(f"  📊 {r['status']}")
        if r.get("updated"):
            lines.append(f"  📅 {r['updated']}")
        if r.get("url"):
            lines.append(f"  🔗 {r['url']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_resume(resume_id: str) -> str:
    """
    Получить детальную информацию о резюме.

    Args:
        resume_id: ID резюме

    Returns:
        Детали резюме
    """
    service = await get_resume_service()
    resume = await service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    lines = [
        f"📄 {resume.get('title', '')}",
        f"{'=' * 50}",
    ]

    if resume.get("name"):
        lines.append(f"👤 {resume['name']}")
    if resume.get("salary"):
        lines.append(f"💰 {resume['salary']}")

    if resume.get("skills"):
        lines.append("")
        lines.append("🔧 Навыки:")
        for skill in resume["skills"][:10]:
            lines.append(f"   • {skill}")

    if resume.get("experience"):
        lines.append("")
        lines.append("💼 Опыт:")
        for exp in resume["experience"][:3]:
            lines.append(f"   • {exp}")

    return "\n".join(lines)


@mcp.tool()
async def hh_update_resume(
    resume_id: str,
    title: str | None = None,
    salary: int | None = None,
    about: str | None = None,
) -> str:
    """
    Обновить резюме.

    Args:
        resume_id: ID резюме
        title: Новая должность
        salary: Новая зарплата
        about: Новый раздел "О себе"

    Returns:
        Результат обновления
    """
    service = await get_resume_service()
    result = await service.update_resume(resume_id, title, salary, about)

    if "error" in result:
        return f"❌ Ошибка: {result['error']}"

    return "✅ Резюме обновлено!"


# ============================================================================
# MCP TOOLS: Отклики (10-11)
# ============================================================================


@mcp.tool()
async def hh_apply_vacancy(
    vacancy_id: str,
    cover_letter: str | None = None,
) -> str:
    """
    Откликнуться на вакансию. Письмо генерируется автоматически через AI.

    Args:
        vacancy_id: ID вакансии
        cover_letter: Сопроводительное письмо (если не передано — сгенерируется через AI)

    Returns:
        Результат отклика
    """
    # Если письмо не передано — генерируем всегда
    if not cover_letter:
        try:
            vacancy_service = await get_vacancy_service()
            vacancy = await vacancy_service.get_vacancy(vacancy_id)
            letter_gen = get_letter_gen()
            cover_letter = await letter_gen.generate_letter(
                vacancy=vacancy, resume=None
            )
        except Exception as e:
            logger.warning(f"Не удалось сгенерировать письмо: {e}")

    service = await get_apply_service()
    result = await service.apply(vacancy_id, cover_letter)

    if "error" in result:
        return f"❌ Ошибка: {result['error']}"

    letter_status = "прикреплено" if result.get("letter_attached") else "не прикреплено"
    lines = [
        "✅ Отклик отправлен!",
        "",
        f"📌 Вакансия: {vacancy_id}",
        f"📝 Письмо: {letter_status}",
    ]
    if cover_letter and result.get("letter_attached"):
        lines.append(f"📝 Текст: {cover_letter[:120]}...")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_applications() -> str:
    """
    Получить историю откликов.

    Returns:
        История откликов
    """
    service = await get_apply_service()
    applications = await service.get_applications()

    if not applications:
        return "Активных откликов нет"

    lines = [f"📬 Активные отклики ({len(applications)}):", ""]

    for app in applications[:10]:
        lines.append(f"📌 {app.get('title', '')}")
        if app.get("company"):
            lines.append(f"   🏢 {app['company']}")
        if app.get("status"):
            lines.append(f"   📊 {app['status']}")
        if app.get("date"):
            lines.append(f"   📅 {app['date']}")
        if app.get("url"):
            lines.append(f"   🔗 {app['url']}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# MCP TOOLS: AI (12-19)
# ============================================================================


@mcp.tool()
async def hh_score_vacancy(
    vacancy_id: str,
    resume_id: str | None = None,
    expected_salary: int | None = None,
) -> str:
    """
    Оценить релевантность вакансии (AI скоринг 0-100).

    Args:
        vacancy_id: ID вакансии
        resume_id: ID резюме (для персонализации)
        expected_salary: Ожидаемая зарплата

    Returns:
        Оценка релевантности
    """
    vacancy_service = await get_vacancy_service()
    vacancy = await vacancy_service.get_vacancy(vacancy_id)

    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"

    scorer = get_ai_scorer()
    scored = scorer.score_vacancy(vacancy, expected_salary=expected_salary)

    lines = [
        f"📊 AI Скоринг: {vacancy.get('title', '')}",
        f"{'=' * 50}",
        "",
        f"🎯 Score: {scored.score}/100 — {scored.score_comment}",
        "",
    ]

    if scored.score_details:
        lines.append("📋 Детали:")
        for key, value in scored.score_details.items():
            lines.append(f"   • {key}: {value}")

    return "\n".join(lines)


@mcp.tool()
async def hh_generate_letter(
    vacancy_id: str,
    resume_id: str | None = None,
) -> str:
    """
    Сгенерировать сопроводительное письмо с AI.

    Args:
        vacancy_id: ID вакансии
        resume_id: ID резюме (для персонализации)

    Returns:
        Сопроводительное письмо
    """
    vacancy_service = await get_vacancy_service()
    vacancy = await vacancy_service.get_vacancy(vacancy_id)

    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"

    letter_gen = get_letter_gen()

    # TODO: Получить резюме если передан resume_id
    letter = await letter_gen.generate_letter(vacancy=vacancy, resume=None)

    return letter_gen.format_letter_for_display(letter, for_llm=True)


@mcp.tool()
async def hh_market_analytics(text: str = "AI разработчик") -> str:
    """
    Проанализировать рынок труда по запросу.

    Args:
        text: Поисковый запрос (должность)

    Returns:
        Аналитика: зарплаты, топ навыки, топ компании, требования к опыту
    """
    from collections import Counter

    from src.ai.scorer import _parse_salary_string

    vacancy_service = await get_vacancy_service()
    result = await vacancy_service.search(text=text, per_page=20)

    if "error" in result:
        return f"❌ Ошибка: {result['error']}"

    vacancies = result.get("vacancies", [])
    if not vacancies:
        return f"❌ По запросу '{text}' вакансий не найдено"

    # Собираем данные
    salaries_from, salaries_to = [], []
    companies = Counter()
    skills_counter = Counter()
    remote_count = 0

    for v in vacancies:
        salary_str = v.get("salary", "") or ""
        f, t = _parse_salary_string(salary_str)
        if f:
            salaries_from.append(f)
        if t:
            salaries_to.append(t)
        if v.get("company"):
            companies[v["company"]] += 1
        for s in v.get("skills", []):
            skills_counter[s.lower()] += 1
        if v.get("remote"):
            remote_count += 1

    total = len(vacancies)
    lines = [
        f"📊 Анализ рынка: {text}",
        f"{'=' * 50}",
        f"📈 Вакансий: {total} | 🏠 Удалённых: {remote_count} ({round(remote_count / total * 100)}%)",
        "",
    ]

    # Зарплаты
    lines.append("💰 Зарплаты:")
    if salaries_from:
        lines.append(
            f"   От: мин {min(salaries_from):,} / средн {sum(salaries_from) // len(salaries_from):,} / макс {max(salaries_from):,} ₽"
        )
    if salaries_to:
        lines.append(
            f"   До: мин {min(salaries_to):,} / средн {sum(salaries_to) // len(salaries_to):,} / макс {max(salaries_to):,} ₽"
        )
    if not salaries_from and not salaries_to:
        lines.append("   Зарплата не указана в большинстве вакансий")

    # Топ навыки
    if skills_counter:
        lines += ["", "🔧 Топ-10 навыков:"]
        for skill, count in skills_counter.most_common(10):
            lines.append(f"   • {skill.title()} — {round(count / total * 100)}%")

    # Топ компании
    if companies:
        lines += ["", "🏢 Топ компании:"]
        for company, count in companies.most_common(5):
            lines.append(f"   • {company} ({count})")

    return "\n".join(lines)


@mcp.tool()
async def hh_start_monitor(interval: int = 300) -> str:
    """
    Запустить мониторинг ответов на отклики.

    Периодически проверяет статусы откликов на hh.ru и уведомляет
    об изменениях (Console + Telegram если настроен TELEGRAM_BOT_TOKEN).

    Args:
        interval: Интервал проверки в секундах (по умолчанию 300 = 5 мин)

    Returns:
        Статус запуска
    """
    monitor = await get_monitor(interval=interval)
    return await monitor.start()


@mcp.tool()
async def hh_stop_monitor() -> str:
    """
    Остановить мониторинг откликов.

    Returns:
        Статус остановки
    """
    monitor = await get_monitor()
    return await monitor.stop()


@mcp.tool()
async def hh_check_monitor() -> str:
    """
    Разово проверить изменения статусов откликов (без запуска фонового цикла).

    Returns:
        Список изменений или "Изменений нет"
    """
    monitor = await get_monitor()
    return await monitor.check_now()


@mcp.tool()
async def hh_career_advisor(
    resume_id: str, vacancy_text: str = "AI разработчик"
) -> str:
    """
    AI Карьерный советник — анализ резюме vs целевые вакансии.

    Args:
        resume_id: ID резюме
        vacancy_text: Текст поиска целевых вакансий

    Returns:
        Полный карьерный отчёт: пробелы, дорожная карта, прогноз зарплаты
    """
    from src.config import MY_EXPECTED_SALARY, MY_SKILLS

    resume_service = await get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = await get_vacancy_service()
    result = await vacancy_service.search(text=vacancy_text, per_page=20)
    vacancies = result.get("vacancies", [])

    advisor = get_career_advisor()

    # Навыки из резюме + дополняем MY_SKILLS
    resume_skills = resume.get("skills", [])
    all_skills = list(set(resume_skills + MY_SKILLS))

    # Собираем навыки из вакансий
    from collections import Counter

    vacancy_skills_counter = Counter()
    for v in vacancies:
        for s in v.get("skills", []):
            vacancy_skills_counter[s.lower()] += 1

    total = len(vacancies) or 1
    my_skills_lower = set(s.lower() for s in all_skills)

    matched = [
        (s, c)
        for s, c in vacancy_skills_counter.most_common(30)
        if s in my_skills_lower
    ]
    missing = [
        (s, c)
        for s, c in vacancy_skills_counter.most_common(30)
        if s not in my_skills_lower
    ]

    lines = [
        "🎯 AI Карьерный советник",
        "=" * 60,
        "",
        f"👤 {resume.get('title', vacancy_text)}",
        f"📅 Опыт: {len(resume.get('experience', []))} мест работы",
        f"🔍 Вакансий проанализировано: {len(vacancies)}",
        "",
        f"✅ Ваши навыки совпадают ({len(matched)}):",
    ]
    for skill, count in matched[:8]:
        pct = round(count / total * 100)
        lines.append(f"   • {skill.title()} — в {pct}% вакансий")

    lines += ["", f"⚠️ Навыки которых не хватает ({len(missing)}):"]
    for skill, count in missing[:8]:
        pct = round(count / total * 100)
        bonus = advisor.skill_salary_bonuses.get(skill, 0)
        bonus_str = f" | +{bonus:,} ₽" if bonus else ""
        lines.append(f"   • {skill.title()} — в {pct}% вакансий{bonus_str}")

    # Прогноз зарплаты по топ-5 missing
    top_missing_skills = [s for s, _ in missing[:5]]
    if top_missing_skills:
        forecast = advisor.forecast_salary(
            current_salary=MY_EXPECTED_SALARY,
            current_skills=all_skills,
            target_skills=top_missing_skills,
            timeline_months=6,
        )
        if "error" not in forecast:
            lines += [
                "",
                "💰 Прогноз зарплаты (если освоить топ-5 недостающих):",
                f"   Сейчас: {forecast['current_salary']:,} ₽",
                f"   Потенциал: {forecast['forecast_salary']:,} ₽ (+{forecast['growth_percentage']}%)",
            ]

    return "\n".join(lines)


@mcp.tool()
async def hh_skills_gap(resume_id: str, vacancy_text: str = "AI разработчик") -> str:
    """
    Анализ пробелов в навыках — резюме vs реальные вакансии.

    Args:
        resume_id: ID резюме
        vacancy_text: Текст поиска вакансий для сравнения

    Returns:
        Топ навыков которых не хватает + которые уже есть
    """
    from collections import Counter

    from src.config import MY_SKILLS

    resume_service = await get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = await get_vacancy_service()
    result = await vacancy_service.search(text=vacancy_text, per_page=20)
    vacancies = result.get("vacancies", [])

    if not vacancies:
        return f"❌ Вакансии по запросу '{vacancy_text}' не найдены"

    # Объединяем навыки резюме + MY_SKILLS (из .env)
    resume_skills = resume.get("skills", [])
    my_skills_lower = set(s.lower() for s in resume_skills + MY_SKILLS)

    # Считаем навыки по вакансиям
    counter = Counter()
    for v in vacancies:
        for s in v.get("skills", []):
            counter[s.lower()] += 1

    total = len(vacancies)
    matched = [(s, c) for s, c in counter.most_common(40) if s in my_skills_lower]
    missing = [(s, c) for s, c in counter.most_common(40) if s not in my_skills_lower]

    match_pct = round(len(matched) / max(len(counter), 1) * 100)

    lines = [
        "🔧 Анализ пробелов в навыках",
        f"{'=' * 50}",
        f"🔍 Запрос: {vacancy_text} ({total} вакансий)",
        f"📊 Покрытие навыков: {match_pct}%",
        "",
        f"✅ Есть ({len(matched)}):",
    ]
    for skill, count in matched[:10]:
        lines.append(f"   • {skill.title()} — {round(count / total * 100)}% вакансий")

    lines += ["", f"❌ Не хватает ({len(missing)}):"]
    advisor = get_career_advisor()
    for skill, count in missing[:10]:
        pct = round(count / total * 100)
        tip = advisor.learning_recommendations.get(skill, "")
        tip_str = f"\n     → {tip}" if tip else ""
        lines.append(f"   • {skill.title()} — {pct}% вакансий{tip_str}")

    return "\n".join(lines)


@mcp.tool()
async def hh_resume_optimizer(
    resume_id: str, vacancy_text: str = "AI разработчик"
) -> str:
    """
    Оптимизировать резюме — конкретные рекомендации на основе реальных вакансий.

    Args:
        resume_id: ID резюме
        vacancy_text: Целевые вакансии для сравнения

    Returns:
        Конкретные рекомендации по улучшению резюме
    """
    from collections import Counter

    from src.config import MY_GITHUB, MY_SKILLS

    resume_service = await get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = await get_vacancy_service()
    result = await vacancy_service.search(text=vacancy_text, per_page=20)
    vacancies = result.get("vacancies", [])

    resume_skills = resume.get("skills", [])
    my_skills_lower = set(s.lower() for s in resume_skills + MY_SKILLS)

    counter = Counter()
    for v in vacancies:
        for s in v.get("skills", []):
            counter[s.lower()] += 1

    total = len(vacancies) or 1
    # Топ-5 навыков из вакансий которых нет в резюме
    critical_missing = [
        s for s, _ in counter.most_common(20) if s not in my_skills_lower
    ][:5]

    lines = [
        "📝 Оптимизация резюме",
        "=" * 50,
        "",
        f"👤 {resume.get('title', '')}",
        f"🔧 Навыков в резюме: {len(resume_skills)}",
        f"🔍 Сравнение с: {len(vacancies)} вакансиями '{vacancy_text}'",
        "",
        "💡 Конкретные рекомендации:",
    ]

    n = 1

    # 1. Навыки которых не хватает
    if critical_missing:
        lines.append(f"   {n}. Добавить в навыки резюме:")
        for s in critical_missing:
            pct = round(counter[s] / total * 100)
            lines.append(f"      • {s.title()} (требуется в {pct}% вакансий)")
        n += 1

    # 2. Раздел "О себе"
    about = resume.get("about", "") or ""
    if len(about) < 200:
        lines.append(
            f"   {n}. Раздел 'О себе' слишком короткий ({len(about)} симв). "
            "Опишите специализацию, проекты, подход к работе. Цель: 300-500 символов."
        )
        n += 1

    # 3. GitHub
    if MY_GITHUB and MY_GITHUB not in about:
        lines.append(
            f"   {n}. Добавьте ссылку на GitHub ({MY_GITHUB}) в раздел 'О себе' или контакты"
        )
        n += 1

    # 4. Метрики в опыте
    experience = resume.get("experience", [])
    short_exp = [e for e in experience if len(str(e)) < 150]
    if short_exp:
        lines.append(
            f"   {n}. В {len(short_exp)} местах работы описание слишком короткое — "
            "добавьте конкретные результаты: объём данных, кол-во запросов, % улучшений"
        )
        n += 1

    # 5. Зарплата
    salary = resume.get("salary")
    if not salary:
        lines.append(f"   {n}. Укажите желаемую зарплату — вакансии лучше матчатся")
        n += 1

    if n == 1:
        lines.append("   ✅ Резюме выглядит хорошо по формальным критериям!")

    return "\n".join(lines)


@mcp.tool()
async def hh_salary_forecast(
    current_salary: int,
    skills: str = "kubernetes,docker,system design",
    timeline_months: int = 12,
) -> str:
    """
    Прогноз зарплаты после изучения новых навыков.

    Args:
        current_salary: Текущая зарплата
        skills: Список навыков через запятую
        timeline_months: Таймлайн в месяцах

    Returns:
        Прогноз зарплаты
    """
    advisor = get_career_advisor()

    skills_list = [s.strip() for s in skills.split(",")]

    forecast = advisor.forecast_salary(
        current_salary=current_salary,
        current_skills=[],
        target_skills=skills_list,
        timeline_months=timeline_months,
    )

    if "error" in forecast:
        return f"❌ {forecast['error']}"

    lines = [
        "💰 Прогноз зарплаты",
        f"{'=' * 50}",
        "",
        f"📊 Текущая зарплата: {forecast['current_salary']:,} ₽",
        f"🎯 Потенциальная: {forecast['forecast_salary']:,} ₽",
        f"📈 Рост: +{forecast['growth_percentage']}% (+{forecast['potential_bonus']:,} ₽)",
        f"📅 Таймлайн: {forecast['timeline_months']} месяцев",
        "",
    ]

    if forecast.get("milestones"):
        lines.append("📚 Вехи:")
        for m in forecast["milestones"]:
            lines.append(
                f"   Месяц {m['month']}: {m['skill'].title()} → {m['new_salary']:,} ₽"
            )

    return "\n".join(lines)


@mcp.tool()
async def hh_health_check() -> str:
    """Диагностика: статус браузера, сессии, лока."""
    info = {
        "browser_initialized": _browser is not None,
        "browser_started": _browser_started,
        "lock_locked": _init_lock.locked(),
        "auth_present": _auth is not None,
        "vacancy_service": _vacancy_service is not None,
        "apply_service": _apply_service is not None,
    }
    if _browser is not None:
        try:
            ctx = getattr(_browser, "_context", None)
            if ctx:
                cookies = await ctx.cookies()
                info["hhtoken_cookie"] = any(
                    c.get("name") == "hhtoken" for c in cookies
                )
                info["pages_open"] = len(ctx.pages)
        except Exception as e:
            info["context_error"] = str(e)
    return "\n".join(f"{k}: {v}" for k, v in info.items())


# ============================================================================
# Запуск
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Запуск {APP_NAME} v{APP_VERSION}")
    logger.info("Требуется: playwright install && playwright install-deps")
    mcp.run()
