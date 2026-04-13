"""
Pydantic модели для вакансий HH.ru.

Определяет структуру данных для:
- Вакансии (полная и краткая)
- Зарплаты
- Работодателя
- Ключевых навыков
- Результатов поиска
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class Salary(BaseModel):
    """Модель зарплаты."""
    
    from_amount: Optional[int] = Field(None, description="Минимальная зарплата")
    to_amount: Optional[int] = Field(None, description="Максимальная зарплата")
    currency: Optional[str] = Field(None, description="Валюта (RUR, USD, EUR)")
    gross: Optional[bool] = Field(None, description="До вычета налогов")
    
    @property
    def formatted(self) -> str:
        """Форматирует зарплату в читаемый вид."""
        if not self.from_amount and not self.to_amount:
            return "Зарплата не указана"
        
        currency_symbols = {
            "RUR": "₽",
            "USD": "$",
            "EUR": "€",
            "KZT": "₸",
            "BYR": "Br",
            "UAH": "₴",
            "AZN": "₼",
            "UZS": "сўм",
            "GEL": "₾",
            "KGT": "сом",
        }
        symbol = currency_symbols.get(self.currency, self.currency or "")
        
        if self.from_amount and self.to_amount:
            return f"{self.from_amount:,} - {self.to_amount:,} {symbol}"
        elif self.from_amount:
            return f"от {self.from_amount:,} {symbol}"
        else:
            return f"до {self.to_amount:,} {symbol}"


class Area(BaseModel):
    """Модель региона/города."""
    
    id: str
    name: str
    url: Optional[str] = None


class Employment(BaseModel):
    """Модель типа занятости."""
    
    id: Optional[str] = None
    name: Optional[str] = None


class Experience(BaseModel):
    """Модель опыта работы."""
    
    id: Optional[str] = None
    name: Optional[str] = None


class KeySkill(BaseModel):
    """Модель ключевого навыка."""
    
    name: str


class Employer(BaseModel):
    """Модель работодателя."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    logos: Optional[list[dict]] = None
    trusted: Optional[bool] = None
    blacklisted: Optional[bool] = None
    
    @property
    def logo_url(self) -> Optional[str]:
        """Получает URL логотипа (90x90)."""
        if self.logos:
            for logo in self.logos:
                if logo.get("original"):
                    return logo["original"]
            for logo in self.logos:
                if logo.get("90"):
                    return logo["90"]
        return None


class VacancyAddress(BaseModel):
    """Модель адреса вакансии."""
    
    city: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    metro_stations: Optional[list[dict]] = None


class Contact(BaseModel):
    """Модель контактной информации."""
    
    name: Optional[str] = None
    email: Optional[str] = None
    phones: Optional[list[dict]] = None
    comment: Optional[str] = None


class DriverLicense(BaseModel):
    """Модель водительских прав."""
    
    type: list[str]


class VacancyBase(BaseModel):
    """Базовая модель вакансии (краткая)."""
    
    id: str
    name: str
    area: Optional[Area] = None
    employer: Optional[Employer] = None
    salary: Optional[Salary] = None
    employment: Optional[Employment] = None
    experience: Optional[Experience] = None
    schedule: Optional[Employment] = None
    snippet: Optional[dict] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    response_url: Optional[str] = None
    archived: Optional[bool] = None
    
    @property
    def short_description(self) -> str:
        """Краткое описание для сниппета."""
        if self.snippet and self.snippet.get("requirement"):
            return self.snippet["requirement"]
        return ""
    
    @property
    def is_remote(self) -> bool:
        """Проверяет удалённая ли работа."""
        if self.schedule and self.schedule.name:
            return "удаленн" in self.schedule.name.lower()
        return False


class VacancyDetail(VacancyBase):
    """Детальная модель вакансии."""
    
    description: Optional[str] = None
    key_skills: Optional[list[KeySkill]] = Field(default_factory=list)
    contacts: Optional[Contact] = None
    working_days: Optional[list[str]] = None
    working_time_intervals: Optional[list[str]] = None
    working_time_modes: Optional[list[str]] = None
    accept_temporary: Optional[bool] = None
    accept_incomplete_resumes: Optional[bool] = None
    accept_handicap: Optional[bool] = None
    driver_license_types: Optional[list[DriverLicense]] = None
    address: Optional[VacancyAddress] = None
    
    # Дополнительные поля для скоринга
    applied_count: Optional[int] = Field(None, description="Количество откликов")
    responding_count: Optional[int] = Field(None, description="Отвечающих работодателей")
    
    @property
    def skills_list(self) -> list[str]:
        """Список навыков."""
        return [skill.name for skill in (self.key_skills or [])]
    
    @property
    def description_plain(self) -> str:
        """Описание без HTML тегов."""
        if not self.description:
            return ""
        import re
        return re.sub(r"<[^>]+>", "", self.description)


class VacancyScored(VacancyDetail):
    """Модель вакансии с AI-скорингом."""
    
    score: int = Field(0, ge=0, le=100, description="AI скоринг релевантности (0-100)")
    score_details: Optional[dict] = Field(None, description="Детали скоринга по категориям")
    score_comment: Optional[str] = Field(None, description="Комментарий к скорингу")


class VacancySearchResult(BaseModel):
    """Модель результата поиска вакансий."""
    
    items: list[VacancyBase] = Field(default_factory=list)
    found: int = Field(0, description="Всего найдено")
    page: int = Field(0, description="Текущая страница")
    pages: int = Field(1, description="Всего страниц")
    per_page: int = Field(20, description="На странице")
    alternate_url: Optional[str] = Field(None, description="URL на hh.ru")
    fixes: Optional[dict] = Field(None, description="Исправления поиска")
    suggests: Optional[dict] = Field(None, description="Подсказки")
    cluster: Optional[list[dict]] = Field(None, description="Кластеры")


class VacancyFilter(BaseModel):
    """Модель фильтров для поиска."""
    
    text: Optional[str] = None
    area: Optional[str] = None
    salary: Optional[int] = None
    only_with_salary: Optional[bool] = True
    experience: Optional[str] = None
    employment: Optional[str] = None
    schedule: Optional[str] = None
    industry: Optional[str] = None
    company_name: Optional[str] = None
    professional_role: Optional[str] = None
    sort: str = Field("publication_time", description="Сортировка: publication_time, salary")
    search_field: str = Field("name", description="Поле поиска: name, description, all")
    period: Optional[int] = Field(None, description="Период в днях")
    page: int = 0
    per_page: int = 20
    
    def to_params(self) -> dict:
        """Конвертирует фильтры в параметры запроса."""
        params = {}
        
        if self.text:
            params["text"] = self.text
        if self.area:
            params["area"] = self.area
        if self.salary:
            params["salary"] = self.salary
        if self.only_with_salary:
            params["only_with_salary"] = "true"
        if self.experience:
            params["experience"] = self.experience
        if self.employment:
            params["employment"] = self.employment
        if self.schedule:
            params["schedule"] = self.schedule
        if self.industry:
            params["industry"] = self.industry
        if self.company_name:
            params["company_name"] = self.company_name
        if self.professional_role:
            params["professional_role"] = self.professional_role
        if self.sort:
            params["sort"] = self.sort
        if self.search_field:
            params["search_field"] = self.search_field
        if self.period:
            params["period"] = self.period
        if self.page:
            params["page"] = self.page
        if self.per_page:
            params["per_page"] = self.per_page
        
        return params


class SimilarVacancies(BaseModel):
    """Модель похожих вакансий."""
    
    items: list[VacancyBase] = Field(default_factory=list)
    total: int = 0


class VacancyStatistics(BaseModel):
    """Модель статистики вакансии."""
    
    views: Optional[int] = None
    responses: Optional[int] = None
    invited: Optional[int] = None
    refused: Optional[int] = None
