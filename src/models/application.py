"""
Pydantic модели для откликов и переговоров.

Определяет структуру данных для:
- Отклика на вакансию
- Истории переговоров
- Статусов откликов
- Приглашений
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VacancyBrief(BaseModel):
    """Краткая модель вакансии для отклика."""
    
    id: str
    name: str
    url: Optional[str] = None
    employer: Optional[dict] = None


class ResumeBrief(BaseModel):
    """Краткая модель резюме для отклика."""
    
    id: str
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class Application(BaseModel):
    """Модель отклика на вакансию."""
    
    id: Optional[str] = None
    vacancy_id: Optional[str] = None
    resume_id: Optional[str] = None
    state: Optional[dict] = None  # Статус отклика
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Вложенные объекты
    vacancy: Optional[VacancyBrief] = None
    resume: Optional[ResumeBrief] = None
    
    # Сопроводительное письмо
    cover_letter: Optional[str] = None
    
    @property
    def status(self) -> str:
        """Получает статус отклика."""
        if self.state and self.state.get("id"):
            return self.state["id"]
        return "unknown"
    
    @property
    def status_name(self) -> str:
        """Получает название статуса."""
        if self.state and self.state.get("name"):
            return self.state["name"]
        return "Неизвестно"
    
    @property
    def vacancy_name(self) -> str:
        """Получает название вакансии."""
        if self.vacancy and self.vacancy.name:
            return self.vacancy.name
        return f"Вакансия {self.vacancy_id}"
    
    @property
    def employer_name(self) -> str:
        """Получает название работодателя."""
        if self.vacancy and self.vacancy.employer:
            return self.vacancy.employer.get("name", "Неизвестно")
        return "Неизвестно"


class ApplicationStatus(BaseModel):
    """Модель статуса отклика."""
    
    id: str = Field(description="ID статуса")
    name: str = Field(description="Название статуса")
    
    # Стандартные статусы hh.ru
    STATUSES = {
        "awaiting_response": "Ожидает ответа",
        "response_received": "Получен ответ",
        "invited": "Приглашение",
        "refused": "Отказ",
        "offer": "Оффер",
        "withdrawn": "Отзыв",
        "no_vacancy": "Вакансия закрыта",
        "blacklisted": "В чёрном списке",
    }
    
    @property
    def is_positive(self) -> bool:
        """Проверяет положительный ли статус."""
        return self.id in ["invited", "offer"]
    
    @property
    def is_negative(self) -> bool:
        """Проверяет отрицательный ли статус."""
        return self.id in ["refused", "blacklisted"]
    
    @property
    def is_pending(self) -> bool:
        """Проверяет ожидает ли ответ."""
        return self.id in ["awaiting_response", "response_received"]
    
    @property
    def emoji(self) -> str:
        """Возвращает эмодзи статуса."""
        emoji_map = {
            "awaiting_response": "⏳",
            "response_received": "📬",
            "invited": "🎉",
            "refused": "❌",
            "offer": "🎊",
            "withdrawn": "↩️",
            "no_vacancy": "🚫",
            "blacklisted": "⛔",
        }
        return emoji_map.get(self.id, "❓")


class Negotiation(BaseModel):
    """Модель переговоров (расширенный отклик)."""
    
    id: Optional[str] = None
    vacancy: Optional[VacancyBrief] = None
    resume: Optional[ResumeBrief] = None
    state: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Ответ работодателя
    answer: Optional[dict] = None
    answer_state: Optional[dict] = None
    
    # Сообщение
    message: Optional[str] = None
    
    @property
    def status(self) -> str:
        """Статус переговоров."""
        if self.state and self.state.get("id"):
            return self.state["id"]
        return "unknown"
    
    @property
    def has_response(self) -> bool:
        """Есть ли ответ от работодателя."""
        return self.answer is not None or self.answer_state is not None
    
    @property
    def response_date(self) -> Optional[datetime]:
        """Дата ответа."""
        if self.answer and self.answer.get("created_at"):
            return datetime.fromisoformat(self.answer["created_at"].replace("Z", "+00:00"))
        return None


class ApplicationStats(BaseModel):
    """Модель статистики откликов."""
    
    total: int = Field(0, description="Всего откликов")
    awaiting: int = Field(0, description="Ожидает ответа")
    invited: int = Field(0, description="Приглашения")
    refused: int = Field(0, description="Отказы")
    offers: int = Field(0, description="Офферы")
    
    @property
    def success_rate(self) -> float:
        """Процент успешных откликов."""
        if self.total == 0:
            return 0.0
        return (self.invited + self.offers) / self.total * 100
    
    @property
    def response_rate(self) -> float:
        """Процент ответов (любых)."""
        if self.total == 0:
            return 0.0
        responded = self.total - self.awaiting
        return responded / self.total * 100


class ApplicationRequest(BaseModel):
    """Модель запроса на отклик."""
    
    vacancy_id: str = Field(description="ID вакансии")
    resume_id: str = Field(description="ID резюме")
    cover_letter: Optional[str] = Field(None, description="Сопроводительное письмо")


class ApplicationStrategy(BaseModel):
    """Модель стратегии отклика."""
    
    strategy: str = Field(
        "manual",
        description="Стратегия: quick (быстрый), smart (AI), manual (ручной)",
    )
    cover_letter: Optional[str] = None
    personalize: bool = Field(True, description="Персонализировать письмо")
    include_skills: bool = Field(True, description="Включить ключевые навыки")
    include_experience: bool = Field(True, description="Включить опыт работы")
