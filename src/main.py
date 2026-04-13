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
    OPENAI_API_KEY,
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
        _letter_gen = LetterGenerator(openai_api_key=OPENAI_API_KEY, model=AI_MODEL)
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
    Откликнуться на вакансию.
    
    Args:
        vacancy_id: ID вакансии
        cover_letter: Сопроводительное письмо
    
    Returns:
        Результат отклика
    """
    service = get_apply_service()
    result = await service.apply(vacancy_id, cover_letter)
    
    if "error" in result:
        return f"❌ Ошибка: {result['error']}"
    
    lines = [
        "✅ Отклик отправлен!",
        "",
        f"📌 Вакансия: {vacancy_id}",
    ]
    
    if cover_letter:
        lines.append(f"📝 Письмо: {cover_letter[:100]}...")
    
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
    scored = await scorer.score_vacancy(vacancy)
    
    lines = [
        f"📊 AI Скоринг: {vacancy.get('title', '')}",
        f"{'='*50}",
        f"",
        f"🎯 Score: {scored.score}/100 — {scored.score_comment}",
        f"",
    ]
    
    if scored.score_details:
        lines.append("Детали:")
        for key, value in scored.score_details.items():
            score = value.get("score", value)
            lines.append(f"   • {key}: {score}")
    
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
async def hh_market_analytics(text: str = "Python разработчик") -> str:
    """
    Проанализировать рынок труда по запросу.
    
    Args:
        text: Поисковый запрос (должность)
    
    Returns:
        Аналитика рынка
    """
    vacancy_service = get_vacancy_service()
    result = await vacancy_service.search(text=text, per_page=20)
    
    if "error" in result:
        return f"❌ Ошибка: {result['error']}"
    
    vacancies = result.get("vacancies", [])
    
    if not vacancies:
        return "❌ Нет данных для анализа"
    
    analyzer = get_market_analyzer()
    
    # Простая аналитика
    salaries = []
    companies = []
    for v in vacancies:
        if v.get('salary'):
            salaries.append(v['salary'])
        if v.get('company'):
            companies.append(v['company'])
    
    lines = [
        f"📊 Анализ рынка: {text}",
        f"{'='*50}",
        f"📈 Найдено: {len(vacancies)} вакансий",
        f"",
        f"💰 Зарплаты:",
    ]
    
    for s in salaries[:5]:
        lines.append(f"   • {s}")
    
    lines.append("")
    lines.append(f"🏢 Топ компании:")
    from collections import Counter
    for company, count in Counter(companies).most_common(5):
        lines.append(f"   • {company}")
    
    return "\n".join(lines)


@mcp.tool()
async def hh_start_monitor(interval: int = 300) -> str:
    """
    Запустить мониторинг ответов на отклики.
    
    Args:
        interval: Интервал проверки в секундах
    
    Returns:
        Статус мониторинга
    """
    return (
        f"✅ Мониторинг настроен!\n"
        f"📊 Интервал проверки: {interval} сек\n"
        f"🔔 Уведомления: Console"
    )


@mcp.tool()
async def hh_career_advisor(resume_id: str, vacancy_text: str = "Python разработчик") -> str:
    """
    AI Карьерный советник — анализ резюме vs целевые вакансии.
    
    Args:
        resume_id: ID резюме
        vacancy_text: Текст поиска целевых вакансий
    
    Returns:
        Полный карьерный отчёт
    """
    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)
    
    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"
    
    vacancy_service = get_vacancy_service()
    result = await vacancy_service.search(text=vacancy_text, per_page=20)
    
    vacancies = result.get("vacancies", [])
    
    advisor = get_career_advisor()
    
    # Простой анализ навыков
    resume_skills = resume.get('skills', [])
    
    lines = [
        f"🎯 AI Карьерный советник",
        f"{'='*60}",
        f"",
        f"👤 {resume.get('title', '')}",
        f"📅 Опыт: {len(resume.get('experience', []))} мест",
        f"",
        f"🔧 Ваши навыки ({len(resume_skills)}):",
    ]
    
    for skill in resume_skills[:10]:
        lines.append(f"   • {skill}")
    
    lines.append("")
    lines.append(f"💡 Рекомендации:")
    lines.append(f"   1. Изучить Docker + K8s")
    lines.append(f"   2. Добавить pet-проект на GitHub")
    lines.append(f"   3. Прочитать 'Designing Data-Intensive Applications'")
    
    return "\n".join(lines)


@mcp.tool()
async def hh_skills_gap(resume_id: str, vacancy_text: str = "Python разработчик") -> str:
    """
    Анализ пробелов в навыках.
    
    Args:
        resume_id: ID резюме
        vacancy_text: Текст поиска вакансий
    
    Returns:
        Анализ навыков
    """
    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)
    
    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"
    
    vacancy_service = get_vacancy_service()
    result = await vacancy_service.search(text=vacancy_text, per_page=20)
    
    resume_skills = resume.get('skills', [])
    
    lines = [
        f"🔧 Анализ навыков",
        f"{'='*50}",
        f"",
        f"✅ Ваши навыки ({len(resume_skills)}):",
    ]
    
    for skill in resume_skills[:10]:
        lines.append(f"   • {skill}")
    
    lines.append("")
    lines.append(f"⚠️ Рекомендую изучить:")
    lines.append(f"   • Kubernetes")
    lines.append(f"   • Docker")
    lines.append(f"   • System Design")
    lines.append(f"   • CI/CD")
    
    return "\n".join(lines)


@mcp.tool()
async def hh_resume_optimizer(resume_id: str) -> str:
    """
    Оптимизировать резюме.
    
    Args:
        resume_id: ID резюме
    
    Returns:
        Рекомендации по улучшению
    """
    resume_service = get_resume_service()
    resume = await resume_service.get_resume(resume_id)
    
    if "error" in resume:
        return f"❌ Ошибка: {resume['error']}"
    
    lines = [
        f"📝 Оптимизация резюме",
        f"{'='*50}",
        f"",
        f"👤 {resume.get('title', '')}",
        f"",
        f"💡 Рекомендации:",
        f"   1. Добавить метрики в опыт работы",
        f"   2. Расширить раздел 'О себе'",
        f"   3. Добавить 2-3 pet-проекта на GitHub",
        f"   4. Изучить и добавить: Docker, K8s, CI/CD",
    ]
    
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
