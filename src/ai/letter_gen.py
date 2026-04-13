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

logger = logging.getLogger(__name__)


class LetterGenerator:
    """
    Генератор сопроводительных писем.
    
    Поддерживает два режима:
    1. LLM (OpenAI) — генерация через AI
    2. Template-based — генерация из шаблонов (без API ключа)
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.openai_api_key = openai_api_key
        self.model = model
        self._client = None
        
        if openai_api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI клиент инициализирован")
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
        
        Args:
            vacancy: Вакансия
            resume: Резюме (опционально)
            personalize: Персонализировать под резюме
            
        Returns:
            Строка с письмом
        """
        if self._client and personalize and resume:
            # Используем LLM
            return await self._generate_with_llm(vacancy, resume)
        else:
            # Используем шаблоны
            return self._generate_from_template(vacancy, resume)
    
    async def _generate_with_llm(self, vacancy: VacancyDetail, resume: ResumeDetail) -> str:
        """
        Генерирует письмо через LLM (OpenAI).
        
        Args:
            vacancy: Вакансия
            resume: Резюме
            
        Returns:
            Строка с письмом
        """
        if not self._client:
            return self._generate_from_template(vacancy, resume)
        
        # Формируем промпт
        prompt = self._build_llm_prompt(vacancy, resume)
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный HR-консультант. Пишешь качественные сопроводительные письма на русском языке. Письмо должно быть кратким (150-250 слов), конкретным и показывать мотивацию кандидата.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            letter = response.choices[0].message.content.strip()
            logger.info("Сопроводительное письмо сгенерировано через LLM")
            return letter
            
        except Exception as e:
            logger.error(f"Ошибка генерации через LLM: {e}")
            return self._generate_from_template(vacancy, resume)
    
    def _build_llm_prompt(self, vacancy: VacancyDetail, resume: ResumeDetail) -> str:
        """Строит промпт для LLM."""
        prompt = f"""
Напиши сопроводительное письмо для следующей вакансии:

**Вакансия:** {vacancy.name}
**Компания:** {vacancy.employer.name if vacancy.employer else "Не указано"}

**Требования:**
{vacancy.description_plain[:500] if vacancy.description else "Не указаны"}

**Ключевые навыки:** {", ".join(vacancy.skills_list[:10]) if vacancy.skills_list else "Не указаны"}

---

**Моё резюме:**

**Опыт работы:** {resume.total_experience_formatted}
**Последняя должность:** {resume.experience[0].position if resume.experience else "Не указано"}
**Компания:** {resume.experience[0].company if resume.experience else "Не указано"}

**Навыки:** {", ".join(resume.skills_flat_list[:15])}

**О себе:** {resume.about[:200] if resume.about else "Не указано"}

---

Напиши письмо, которое:
1. Показывает интерес к компании и вакансии
2. Подчёркивает релевантный опыт и навыки
3. Конкретно (не общо) объясняет почему я подхожу
4. Завершается призывом к действию

Пиши на русском языке. 150-250 слов.
"""
        return prompt
    
    def _generate_from_template(
        self,
        vacancy: VacancyDetail,
        resume: Optional[ResumeDetail] = None,
    ) -> str:
        """
        Генерирует письмо из шаблона.
        
        Args:
            vacancy: Вакансия
            resume: Резюме (опционально)
            
        Returns:
            Строка с письмом
        """
        company_name = vacancy.employer.name if vacancy.employer else "вашей компании"
        vacancy_name = vacancy.name
        
        if resume:
            # Персонализированный шаблон
            experience = resume.total_experience_formatted
            latest_position = resume.experience[0].position if resume.experience else "разработчик"
            skills = ", ".join(resume.skills_flat_list[:5]) if resume.skills_flat_list else "соответствующие навыки"
            
            letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в компании {company_name}.

Мой опыт работы в IT составляет {experience}. На текущий момент я работаю в должностива "{latest_position}", где занимаюсь разработкой и поддержанием программных продуктов.

Мои ключевые навыки: {skills}.

Я уверен, что мой опыт и компетенции будут полезны вашей команде. Буду рад обсудить детали на собеседовании.

С уважением,
{resume.full_name if resume else "Кандидат"}
"""
        else:
            # Базовый шаблон
            letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в компании {company_name}.

У меня есть релевантный опыт работы и навыки, необходимые для данной позиции. Буду рад внести свой вклад в развитие вашей команды.

Буду рад обсудить детали на собеседовании.

С уважением,
Кандидат
"""
        
        logger.info("Сопроводительное письмо сгенерировано из шаблона")
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
