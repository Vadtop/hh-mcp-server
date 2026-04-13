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
from typing import Optional

from fastmcp import FastMCP

from src.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    OPENROUTER_API_KEY,
    AI_MODEL,
)
from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.services.vacancy import VacancyService
from src.services.resume import ResumeService
from src.services.apply import ApplyService
from src.ai.scorer import AIVacancyScorer
from src.ai.letter_gen import LetterGenerator
from src.ai.market_analyzer import MarketAnalyzer
from src.ai.career_advisor import CareerAdvisor
from src.services.monitor import MonitorService

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# MCP сервер
mcp = FastMCP(APP_NAME)

# Глобальные объекты
_browser: Optional[BrowserEngine] = None
_vacancy_service: Optional[VacancyService] = None
_resume_service: Optional[ResumeService] = None
_apply_service: Optional[ApplyService] = None
_ai_scorer: Optional[AIVacancyScorer] = None
_letter_gen: Optional[LetterGenerator] = None
_market_analyzer: Optional[MarketAnalyzer] = None
_career_advisor: Optional[CareerAdvisor] = None
_monitor: Optional[MonitorService] = None


def get_browser() -> BrowserEngine:
    global _browser
    if _browser is None:
        _browser = BrowserEngine(headless=True, slow_mo=50)
    return _browser


def get_vacancy_service() -> VacancyService:
    global _vacancy_service
    if _vacancy_service is None:
        _vacancy_service = VacancyService(get_browser())
    return _vacancy_service


def get_resume_service() -> ResumeService:
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService(get_browser())
    return _resume_service


def get_apply_service() -> ApplyService:
    global _apply_service
    if _apply_service is None:
        _apply_service = ApplyService(get_browser())
    return _apply_service


def get_ai_scorer() -> AIVacancyScorer:
    global _ai_scorer
    if _ai_scorer is None:
        _ai_scorer = AIVacancyScorer()
    return _ai_scorer


def get_letter_gen() -> LetterGenerator:
    global _letter_gen
    if _letter_gen is None:
        _letter_gen = LetterGenerator(openrouter_api_key=OPENROUTER_API_KEY, model=AI_MODEL)
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


def get_monitor(interval: int = 300) -> MonitorService:
    global _monitor
    if _monitor is None:
        _monitor = MonitorService(apply_service=get_apply_service(), interval=interval)
    return _monitor


# ============================================================================
# MCP TOOLS: Вакансии (1-6)
# ============================================================================

@mcp.tool()
async def hh_search(
    text: str,
    area: Optional[str] = None,
    salary: Optional[int] = None,
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
    service = get_vacancy_service()

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
    
    for i, v in enumerate(vacancies[:10], 1):
        lines.append(f"{i}. {v.get('title', '')}")
        if v.get('company'):
            lines.append(f"   🏢 {v['company']}")
        if v.get('salary'):
            lines.append(f"   💰 {v['salary']}")
        if v.get('location'):
            lines.append(f"   📍 {v['location']}")
        if v.get('url'):
            lines.append(f"   🔗 {v['url']}")
        lines.append("")
    
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
    service = get_vacancy_service()
    vacancy = await service.get_vacancy(vacancy_id)
    
    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"
    
    lines = [
        f"📌 {vacancy.get('title', '')}",
        f"{'='*50}",
    ]
    
    if vacancy.get('company'):
        lines.append(f"🏢 {vacancy['company']}")
    if vacancy.get('salary'):
        lines.append(f"💰 {vacancy['salary']}")
    if vacancy.get('experience'):
        lines.append(f"💼 Опыт: {vacancy['experience']}")
    if vacancy.get('employment'):
        lines.append(f"📋 {vacancy['employment']}")
    if vacancy.get('location'):
        lines.append(f"📍 {vacancy['location']}")
    
    if vacancy.get('skills'):
        lines.append("")
        lines.append("🔧 Навыки:")
        for skill in vacancy['skills'][:10]:
            lines.append(f"   • {skill}")
    
    if vacancy.get('url'):
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
    service = get_vacancy_service()
    employer = await service.get_employer(employer_id)
    
    if "error" in employer:
        return f"❌ Ошибка: {employer['error']}"
    
    lines = [
        f"🏢 {employer.get('name', 'Неизвестно')}",
        f"{'='*50}",
    ]
    
    if employer.get('description'):
        lines.append(employer['description'][:500])
    
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
    service = get_vacancy_service()
    similar = await service.get_similar(vacancy_id)
    
    if not similar:
        return "Похожих вакансий не найдено"
    
    lines = [f"🔍 Похожие вакансии ({len(similar)}):", ""]
    
    for i, v in enumerate(similar[:5], 1):
        lines.append(f"{i}. {v.get('title', '')}")
        if v.get('company'):
            lines.append(f"   🏢 {v['company']}")
        if v.get('salary'):
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
    service = get_resume_service()
    resumes = await service.get_my_resumes()
    
    if not resumes:
        return "Резюме не найдены"
    
    lines = [f"📄 Мои резюме ({len(resumes)}):", ""]
    
    for r in resumes:
        lines.append(f"• {r.get('title', '')}")
        if r.get('status'):
            lines.append(f"  📊 {r['status']}")
        if r.get('updated'):
            lines.append(f"  📅 {r['updated']}")
        if r.get('url'):
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
    service = get_resume_service()
    resume = await service.get_resume(resume_id)
    
    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"
    
    lines = [
        f"📄 {resume.get('title', '')}",
        f"{'='*50}",
    ]
    
    if resume.get('name'):
        lines.append(f"👤 {resume['name']}")
    if resume.get('salary'):
        lines.append(f"💰 {resume['salary']}")
    
    if resume.get('skills'):
        lines.append("")
        lines.append("🔧 Навыки:")
        for skill in resume['skills'][:10]:
            lines.append(f"   • {skill}")
    
    if resume.get('experience'):
        lines.append("")
        lines.append("💼 Опыт:")
        for exp in resume['experience'][:3]:
            lines.append(f"   • {exp}")
    
    return "\n".join(lines)


@mcp.tool()
async def hh_update_resume(
    resume_id: str,
    title: Optional[str] = None,
    salary: Optional[int] = None,
    about: Optional[str] = None,
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
    service = get_resume_service()
    result = await service.update_resume(resume_id, title, salary, about)
    
    if "error" in result:
        return f"❌ Ошибка: {result['error']}"
    
    return f"✅ Резюме обновлено!"


# ============================================================================
# MCP TOOLS: Отклики (10-11)
# ============================================================================

@mcp.tool()
async def hh_apply_vacancy(
    vacancy_id: str,
    cover_letter: Optional[str] = None,
) -> str:
    """
    Откликнуться на вакансию. Если вакансия требует письмо — генерирует автоматически.

    Args:
        vacancy_id: ID вакансии
        cover_letter: Сопроводительное письмо (если не передано — сгенерируется через AI)

    Returns:
        Результат отклика
    """
    service = get_apply_service()
    result = await service.apply(vacancy_id, cover_letter)

    # Вакансия требует письмо — генерируем и повторяем
    if result.get("needs_letter") and not cover_letter:
        logger.info(f"Вакансия {vacancy_id} требует письмо — генерируем через AI")
        try:
            vacancy_service = get_vacancy_service()
            vacancy = await vacancy_service.get_vacancy(vacancy_id)
            letter_gen = get_letter_gen()
            cover_letter = await letter_gen.generate_letter(vacancy=vacancy)
            # Повторяем отклик с письмом
            result = await service.apply(vacancy_id, cover_letter)
        except Exception as e:
            return f"❌ Не удалось сгенерировать письмо: {e}"

    if "error" in result:
        return f"❌ Ошибка: {result['error']}"

    lines = [
        "✅ Отклик отправлен!",
        "",
        f"📌 Вакансия: {vacancy_id}",
    ]
    if cover_letter:
        lines.append(f"📝 Письмо: {cover_letter[:120]}...")

    return "\n".join(lines)


@mcp.tool()
async def hh_get_applications() -> str:
    """
    Получить историю откликов.
    
    Returns:
        История откликов
    """
    service = get_apply_service()
    applications = await service.get_applications()
    
    if not applications:
        return "Активных откликов нет"
    
    lines = [f"📬 Активные отклики ({len(applications)}):", ""]
    
    for app in applications[:10]:
        lines.append(f"📌 {app.get('title', '')}")
        if app.get('company'):
            lines.append(f"   🏢 {app['company']}")
        if app.get('status'):
            lines.append(f"   📊 {app['status']}")
        if app.get('date'):
            lines.append(f"   📅 {app['date']}")
        if app.get('url'):
            lines.append(f"   🔗 {app['url']}")
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# MCP TOOLS: AI (12-19)
# ============================================================================

@mcp.tool()
async def hh_score_vacancy(
    vacancy_id: str,
    resume_id: Optional[str] = None,
    expected_salary: Optional[int] = None,
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
    vacancy_service = get_vacancy_service()
    vacancy = await vacancy_service.get_vacancy(vacancy_id)
    
    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"
    
    scorer = get_ai_scorer()
    scored = scorer.score_vacancy(vacancy, expected_salary=expected_salary)

    lines = [
        f"📊 AI Скоринг: {vacancy.get('title', '')}",
        f"{'='*50}",
        f"",
        f"🎯 Score: {scored.score}/100 — {scored.score_comment}",
        f"",
    ]

    if scored.score_details:
        lines.append("📋 Детали:")
        for key, value in scored.score_details.items():
            lines.append(f"   • {key}: {value}")

    return "\n".join(lines)


@mcp.tool()
async def hh_generate_letter(
    vacancy_id: str,
    resume_id: Optional[str] = None,
) -> str:
    """
    Сгенерировать сопроводительное письмо с AI.
    
    Args:
        vacancy_id: ID вакансии
        resume_id: ID резюме (для персонализации)
    
    Returns:
        Сопроводительное письмо
    """
    vacancy_service = get_vacancy_service()
    vacancy = await vacancy_service.get_vacancy(vacancy_id)
    
    if "error" in vacancy:
        return f"❌ Ошибка: {vacancy['error']}"
    
    letter_gen = get_letter_gen()
    
    # TODO: Получить резюме если передан resume_id
    letter = await letter_gen.generate_letter(vacancy=vacancy, resume=None)
    
    return letter_gen.format_letter_for_display(letter)


@mcp.tool()
async def hh_market_analytics(text: str = "AI разработчик") -> str:
    """
    Проанализировать рынок труда по запросу.

    Args:
        text: Поисковый запрос (должность)

    Returns:
        Аналитика: зарплаты, топ навыки, топ компании, требования к опыту
    """
    from src.ai.scorer import _parse_salary_string
    from collections import Counter

    vacancy_service = get_vacancy_service()
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
        f"{'='*50}",
        f"📈 Вакансий: {total} | 🏠 Удалённых: {remote_count} ({round(remote_count/total*100)}%)",
        "",
    ]

    # Зарплаты
    lines.append("💰 Зарплаты:")
    if salaries_from:
        lines.append(f"   От: мин {min(salaries_from):,} / средн {sum(salaries_from)//len(salaries_from):,} / макс {max(salaries_from):,} ₽")
    if salaries_to:
        lines.append(f"   До: мин {min(salaries_to):,} / средн {sum(salaries_to)//len(salaries_to):,} / макс {max(salaries_to):,} ₽")
    if not salaries_from and not salaries_to:
        lines.append("   Зарплата не указана в большинстве вакансий")

    # Топ навыки
    if skills_counter:
        lines += ["", "🔧 Топ-10 навыков:"]
        for skill, count in skills_counter.most_common(10):
            lines.append(f"   • {skill.title()} — {round(count/total*100)}%")

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
    monitor = get_monitor(interval=interval)
    return await monitor.start()


@mcp.tool()
async def hh_stop_monitor() -> str:
    """
    Остановить мониторинг откликов.

    Returns:
        Статус остановки
    """
    monitor = get_monitor()
    return await monitor.stop()


@mcp.tool()
async def hh_check_monitor() -> str:
    """
    Разово проверить изменения статусов откликов (без запуска фонового цикла).

    Returns:
        Список изменений или "Изменений нет"
    """
    monitor = get_monitor()
    return await monitor.check_now()


@mcp.tool()
async def hh_career_advisor(resume_id: str, vacancy_text: str = "AI разработчик") -> str:
    """
    AI Карьерный советник — анализ резюме vs целевые вакансии.

    Args:
        resume_id: ID резюме
        vacancy_text: Текст поиска целевых вакансий

    Returns:
        Полный карьерный отчёт: пробелы, дорожная карта, прогноз зарплаты
    """
    from src.config import MY_SKILLS, MY_EXPECTED_SALARY

    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = get_vacancy_service()
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

    matched = [(s, c) for s, c in vacancy_skills_counter.most_common(30) if s in my_skills_lower]
    missing = [(s, c) for s, c in vacancy_skills_counter.most_common(30) if s not in my_skills_lower]

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
    from src.config import MY_SKILLS
    from collections import Counter

    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = get_vacancy_service()
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
        f"🔧 Анализ пробелов в навыках",
        f"{'='*50}",
        f"🔍 Запрос: {vacancy_text} ({total} вакансий)",
        f"📊 Покрытие навыков: {match_pct}%",
        "",
        f"✅ Есть ({len(matched)}):",
    ]
    for skill, count in matched[:10]:
        lines.append(f"   • {skill.title()} — {round(count/total*100)}% вакансий")

    lines += ["", f"❌ Не хватает ({len(missing)}):"]
    advisor = get_career_advisor()
    for skill, count in missing[:10]:
        pct = round(count / total * 100)
        tip = advisor.learning_recommendations.get(skill, "")
        tip_str = f"\n     → {tip}" if tip else ""
        lines.append(f"   • {skill.title()} — {pct}% вакансий{tip_str}")

    return "\n".join(lines)


@mcp.tool()
async def hh_resume_optimizer(resume_id: str, vacancy_text: str = "AI разработчик") -> str:
    """
    Оптимизировать резюме — конкретные рекомендации на основе реальных вакансий.

    Args:
        resume_id: ID резюме
        vacancy_text: Целевые вакансии для сравнения

    Returns:
        Конкретные рекомендации по улучшению резюме
    """
    from src.config import MY_SKILLS, MY_GITHUB
    from collections import Counter

    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)

    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"

    vacancy_service = get_vacancy_service()
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
        lines.append(f"   {n}. Добавьте ссылку на GitHub ({MY_GITHUB}) в раздел 'О себе' или контакты")
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
        f"💰 Прогноз зарплаты",
        f"{'='*50}",
        f"",
        f"📊 Текущая зарплата: {forecast['current_salary']:,} ₽",
        f"🎯 Потенциальная: {forecast['forecast_salary']:,} ₽",
        f"📈 Рост: +{forecast['growth_percentage']}% (+{forecast['potential_bonus']:,} ₽)",
        f"📅 Таймлайн: {forecast['timeline_months']} месяцев",
        f"",
    ]
    
    if forecast.get("milestones"):
        lines.append("📚 Вехи:")
        for m in forecast["milestones"]:
            lines.append(f"   Месяц {m['month']}: {m['skill'].title()} → {m['new_salary']:,} ₽")
    
    return "\n".join(lines)


# ============================================================================
# Запуск
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Запуск {APP_NAME} v{APP_VERSION}")
    logger.info("Требуется: playwright install && playwright install-deps")
    mcp.run()
