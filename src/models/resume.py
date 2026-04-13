"""
Pydantic модели для резюме HH.ru.

Определяет структуру данных для:
- Резюме (полное и краткое)
- Опыт работы
- Образование
- Навыки
- Языки
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ResumeExperience(BaseModel):
    """Модель места работы в резюме."""
    
    company: Optional[str] = None
    company_id: Optional[str] = None
    position: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    description: Optional[str] = None
    achievements: Optional[str] = None
    area: Optional[dict] = None
    industries: Optional[list[dict]] = None
    url: Optional[str] = None
    
    @property
    def duration_months(self) -> Optional[int]:
        """Длительность работы в месяцах."""
        if self.start:
            end = self.end or date.today()
            return (end.year - self.start.year) * 12 + (end.month - self.start.month)
        return None
    
    @property
    def duration_formatted(self) -> str:
        """Форматирует длительность."""
        months = self.duration_months
        if months is None:
            return "Не указано"
        years = months // 12
        remaining_months = months % 12
        parts = []
        if years:
            parts.append(f"{years} г." if years == 1 else f"{years} г.")
        if remaining_months:
            parts.append(f"{remaining_months} мес.")
        return " ".join(parts) if parts else "Менее месяца"


class ResumeEducation(BaseModel):
    """Модель образования."""
    
    institution: Optional[str] = None
    organization_id: Optional[str] = None
    faculty: Optional[str] = None
    specialization: Optional[str] = None
    result: Optional[str] = None
    year: Optional[int] = None
    education_level: Optional[str] = None


class ResumeSkill(BaseModel):
    """Модель навыка в резюме."""
    
    name: str
    level: Optional[str] = None  # beginner, intermediate, advanced, expert


class ResumeLanguage(BaseModel):
    """Модель языка."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    level_id: Optional[str] = None
    level: Optional[str] = None  # a1, a2, b1, b2, c1, c2


class ResumeCertificate(BaseModel):
    """Модель сертификата."""
    
    title: Optional[str] = None
    issuing_organization: Optional[str] = None
    issued: Optional[date] = None
    url: Optional[str] = None


class ResumeProject(BaseModel):
    """Модель проекта в резюме."""
    
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None


class ResumeBase(BaseModel):
    """Базовая модель резюме (краткая)."""
    
    id: str
    title: Optional[str] = None  # Должность
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    area: Optional[dict] = None
    salary: Optional[int] = None
    currency: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[dict] = None
    is_published: Optional[bool] = None
    
    @property
    def full_name(self) -> str:
        """Полное имя."""
        parts = [p for p in [self.last_name, self.first_name, self.middle_name] if p]
        return " ".join(parts) or "Не указано"
    
    @property
    def salary_formatted(self) -> str:
        """Форматирует зарплату."""
        if not self.salary:
            return "Зарплата не указана"
        currency_symbols = {
            "RUR": "₽",
            "USD": "$",
            "EUR": "€",
        }
        symbol = currency_symbols.get(self.currency, self.currency or "")
        return f"{self.salary:,} {symbol}"


class ResumeDetail(ResumeBase):
    """Детальная модель резюме."""
    
    # Контактная информация
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    
    # Профессиональная информация
    about: Optional[str] = None  # О себе
    experience: Optional[list[ResumeExperience]] = Field(default_factory=list)
    education: Optional[list[ResumeEducation]] = Field(default_factory=list)
    skills: Optional[list[ResumeSkill]] = Field(default_factory=list)
    languages: Optional[list[ResumeLanguage]] = Field(default_factory=list)
    certificates: Optional[list[ResumeCertificate]] = Field(default_factory=list)
    projects: Optional[list[ResumeProject]] = Field(default_factory=list)
    
    # Дополнительная информация
    citizenship: Optional[list[dict]] = None
    work_experience: Optional[dict] = None  # Общий опыт
    schedule: Optional[dict] = None  # График работы
    employment: Optional[dict] = None  # Тип занятости
    
    # Специальные поля
    hidden_fields: Optional[list[dict]] = None
    
    @property
    def total_experience_months(self) -> int:
        """Общий опыт работы в месяцах."""
        total = 0
        for exp in self.experience or []:
            if exp.duration_months:
                total += exp.duration_months
        return total
    
    @property
    def total_experience_formatted(self) -> str:
        """Форматирует общий опыт."""
        months = self.total_experience_months
        years = months // 12
        remaining = months % 12
        
        parts = []
        if years:
            parts.append(f"{years} г." if years == 1 else f"{years} г.")
        if remaining:
            parts.append(f"{remaining} мес.")
        
        return " ".join(parts) if parts else "Без опыта"
    
    @property
    def skills_flat_list(self) -> list[str]:
        """Плоский список навыков."""
        return [skill.name for skill in (self.skills or [])]
    
    @property
    def description_plain(self) -> str:
        """Описание без HTML."""
        if not self.about:
            return ""
        import re
        return re.sub(r"<[^>]+>", "", self.about)


class ResumeUpdateRequest(BaseModel):
    """Модель для обновления резюме."""
    
    title: Optional[str] = None
    salary: Optional[int] = None
    currency: Optional[str] = None
    about: Optional[str] = None
    skills: Optional[list[ResumeSkill]] = None
    schedule: Optional[dict] = None
    employment: Optional[dict] = None


class ResumeStatistics(BaseModel):
    """Модель статистики резюме."""
    
    views: Optional[int] = None
    views_today: Optional[int] = None
    responses: Optional[int] = None
    invites: Optional[int] = None
    offers: Optional[int] = None
