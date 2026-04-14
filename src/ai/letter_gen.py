"""
AI-генератор сопроводительных писем.

Реализует:
- Генерация персонализированных писем на основе вакансии и резюме
- Шаблоны писем для разных сценариев
- Интеграция с OpenAI API (опционально)
- Fallback на шаблоны без LLM
"""

import logging
from typing import Optional
from datetime import datetime

from src.models.vacancy import VacancyDetail
from src.models.resume import ResumeDetail
from src.config import MY_RESUME_TEXT, MY_SKILLS, MY_GITHUB, MY_TELEGRAM, MY_NAME

logger = logging.getLogger(__name__)


def _build_profile_prompt() -> str:
    """Строит системный промпт из конфига (не хардкод — данные в .env)."""
    github_line = f"**GitHub:** {MY_GITHUB}" if MY_GITHUB else ""
    telegram_line = f"**Telegram:** {MY_TELEGRAM}" if MY_TELEGRAM else ""
    contacts = "\n".join(filter(None, [github_line, telegram_line]))

    return f"""Ты пишешь сопроводительные письма от имени кандидата.

**Профиль кандидата:**
{MY_RESUME_TEXT}
{contacts}

Письмо должно быть:
- Кратким (150-200 слов)
- Конкретным — ссылаться на реальные проекты кандидата
- Показывать связь между опытом кандидата и требованиями вакансии
- На русском языке
- Без воды и общих фраз
- Завершаться призывом обсудить детали"""


class LetterGenerator:
    """
    Генератор сопроводительных писем.

    Поддерживает два режима:
    1. LLM (OpenRouter) — генерация через AI, всегда персональная
    2. Template-based — fallback без API ключа
    """

    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        model: str = "google/gemini-2.5-flash",
    ):
        self.model = model
        self._client = None

        if openrouter_api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                logger.info(f"OpenRouter клиент инициализирован, модель: {model}")
            except ImportError:
                logger.warning("OpenAI пакет не установлен. Используем шаблоны.")

    async def generate_letter(
        self,
        vacancy: VacancyDetail,
        resume: Optional[ResumeDetail] = None,
        personalize: bool = True,
    ) -> str:
        """
        Генерирует сопроводительное письмо.

        Если OpenRouter настроен — всегда использует LLM (резюме не обязательно).
        Иначе — шаблонный fallback.

        Args:
            vacancy: Вакансия
            resume: Резюме (опционально, для дополнительного контекста)
            personalize: Игнорируется, оставлен для совместимости

        Returns:
            Строка с письмом
        """
        if self._client:
            return await self._generate_with_llm(vacancy, resume)
        else:
            return self._generate_from_template(vacancy, resume)

    async def _generate_with_llm(
        self,
        vacancy: VacancyDetail,
        resume: Optional[ResumeDetail] = None,
    ) -> str:
        """
        Генерирует письмо через LLM (OpenRouter).

        Args:
            vacancy: Вакансия
            resume: Резюме (опционально)

        Returns:
            Строка с письмом
        """
        if not self._client:
            return self._generate_from_template(vacancy, resume)

        prompt = self._build_llm_prompt(vacancy, resume)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _build_profile_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )

            letter = response.choices[0].message.content.strip()
            logger.info(f"Письмо сгенерировано через OpenRouter ({self.model})")
            return letter

        except Exception as e:
            logger.error(f"Ошибка генерации через OpenRouter: {e}")
            return self._generate_from_template(vacancy, resume)

    def _build_llm_prompt(
        self,
        vacancy,  # dict или VacancyDetail
        resume=None,
    ) -> str:
        """Строит промпт для LLM. Принимает dict или VacancyDetail."""
        # Универсальное извлечение полей — работает с dict и Pydantic
        if isinstance(vacancy, dict):
            title = vacancy.get("name") or vacancy.get("title", "")
            company = vacancy.get("company", "Не указано")
            skills = vacancy.get("skills", [])
            vacancy_skills = ", ".join(skills[:10]) if skills else "не указаны"
            description = (vacancy.get("description") or "")[:600]
        else:
            title = getattr(vacancy, "name", "")
            employer = getattr(vacancy, "employer", None)
            company = employer.name if employer else "Не указано"
            skills_list = getattr(vacancy, "skills_list", None) or []
            vacancy_skills = (
                ", ".join(skills_list[:10]) if skills_list else "не указаны"
            )
            description = (getattr(vacancy, "description_plain", None) or "")[:600]

        resume_context = ""
        if resume and not isinstance(resume, dict):
            resume_context = f"""
**Дополнительно из резюме:**
- Опыт: {resume.total_experience_formatted}
- Последняя должность: {resume.experience[0].position if resume.experience else "—"}
- Навыки: {", ".join(resume.skills_flat_list[:10])}
"""

        prompt = f"""Напиши сопроводительное письмо для вакансии:

**Вакансия:** {title}
**Компания:** {company}
**Требуемые навыки:** {vacancy_skills}
**Описание:** {description}
{resume_context}
Сделай акцент на релевантных проектах кандидата. Упомяни конкретные технологии из стека, которые совпадают с требованиями вакансии."""

        return prompt

    def _generate_from_template(
        self,
        vacancy: VacancyDetail,
        resume: Optional[ResumeDetail] = None,
    ) -> str:
        """
        Fallback — генерирует письмо из шаблона с профилем кандидата.

        Args:
            vacancy: Вакансия
            resume: Резюме (опционально)

        Returns:
            Строка с письмом
        """
        if isinstance(vacancy, dict):
            vacancy_name = vacancy.get("name") or vacancy.get("title", "")
            company_name = vacancy.get("company", "вашей компании")
        else:
            employer = getattr(vacancy, "employer", None)
            company_name = employer.name if employer else "вашей компании"
            vacancy_name = getattr(vacancy, "name", "")

        contacts = " | ".join(
            filter(
                None,
                [
                    MY_GITHUB and f"GitHub: {MY_GITHUB}",
                    MY_TELEGRAM and f"Telegram: {MY_TELEGRAM}",
                ],
            )
        )

        letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в {company_name}.

{MY_RESUME_TEXT}

{contacts}

Буду рад обсудить детали на собеседовании.

С уважением,
{MY_NAME or "Кандидат"}"""

        logger.info("Сопроводительное письмо сгенерировано из шаблона (fallback)")
        return letter.strip()

    def generate_quick_letter(self, vacancy_name: str, company_name: str) -> str:
        """
        Генерирует быстрое короткое письмо.

        Args:
            vacancy_name: Название вакансии
            company_name: Название компании

        Returns:
            Краткое письмо
        """
        return f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в компании {company_name}. Буду рад обсудить детали на собеседовании.

С уважением,
Кандидат
"""

    def generate_motivated_letter(
        self,
        vacancy: VacancyDetail,
        motivation_reason: str,
        resume: Optional[ResumeDetail] = None,
    ) -> str:
        """
        Генерирует мотивированное письмо с конкретной причиной.

        Args:
            vacancy: Вакансия
            motivation_reason: Причина интереса (например, "хочу работать с K8s")
            resume: Резюме

        Returns:
            Письмо с мотивацией
        """
        company_name = vacancy.employer.name if vacancy.employer else "вашей компании"

        letter = f"""Здравствуйте!

Пишу вам по поводу вакансии "{vacancy.name}" в компании {company_name}.

Меня особенно заинтересовала эта позиция, потому что {motivation_reason}.

{f"Мой опыт работы: {resume.total_experience_formatted}. Последние проекты связаны с: {', '.join(resume.skills_flat_list[:5])}." if resume else ""}

Буду рад возможности внести свой вклад в вашу команду и развиваться в данном направлении.

С уважением,
{resume.full_name if resume else "Кандидат"}
"""

        return letter.strip()

    def format_letter_for_display(self, letter: str) -> str:
        """
        Форматирует письмо для отображения.

        Args:
            letter: Письмо

        Returns:
            Отформатированное письмо
        """
        lines = [
            "📝 Сопроводительное письмо:",
            "─" * 40,
            letter,
            "─" * 40,
            f"📊 Слов: {len(letter.split())}",
            f"📏 Символов: {len(letter)}",
        ]

        return "\n".join(lines)
