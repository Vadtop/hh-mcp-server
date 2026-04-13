"""
Анализатор рынка труда.

Реализует:
- Анализ зарплатных трендов
- Определение востребованных навыков
- Статистику по регионам
- Отчёты и визуализацию
"""

import logging
from typing import Optional
from collections import Counter, defaultdict

from src.models.vacancy import VacancyBase, VacancyDetail

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Анализатор рынка труда на основе данных hh.ru.
    
    Анализирует:
    - Зарплатные диапазоны по профессиям
    - Востребованные навыки
    - Конкуренцию по регионам
    - Тренды
    """
    
    def __init__(self):
        self._vacancies_cache: list[VacancyDetail] = []
    
    def analyze_salaries(self, vacancies: list[VacancyDetail]) -> dict:
        """
        Анализирует зарплаты по вакансиям.
        
        Args:
            vacancies: Список вакансий
            
        Returns:
            dict со статистикой зарплат
        """
        salaries_from = []
        salaries_to = []
        currencies = Counter()
        
        for v in vacancies:
            if v.salary:
                if v.salary.from_amount:
                    salaries_from.append(v.salary.from_amount)
                if v.salary.to_amount:
                    salaries_to.append(v.salary.to_amount)
                if v.salary.currency:
                    currencies[v.salary.currency] += 1
        
        if not salaries_from and not salaries_to:
            return {"error": "Нет данных о зарплатах"}
        
        result = {
            "total_with_salary": len(salaries_from) + len(salaries_to),
            "currencies": dict(currencies),
        }
        
        if salaries_from:
            result["min_from"] = min(salaries_from)
            result["max_from"] = max(salaries_from)
            result["avg_from"] = int(sum(salaries_from) / len(salaries_from))
            result["median_from"] = sorted(salaries_from)[len(salaries_from) // 2]
        
        if salaries_to:
            result["min_to"] = min(salaries_to)
            result["max_to"] = max(salaries_to)
            result["avg_to"] = int(sum(salaries_to) / len(salaries_to))
            result["median_to"] = sorted(salaries_to)[len(salaries_to) // 2]
        
        # Общий средний диапазон
        all_salaries = salaries_from + salaries_to
        if all_salaries:
            result["overall_avg"] = int(sum(all_salaries) / len(all_salaries))
        
        return result
    
    def analyze_skills(self, vacancies: list[VacancyDetail], top_n: int = 20) -> dict:
        """
        Анализирует востребованные навыки.
        
        Args:
            vacancies: Список вакансий
            top_n: Топ N навыков
            
        Returns:
            dict с навыками и частотой
        """
        skills_counter = Counter()
        skills_by_vacancy = defaultdict(list)
        
        for v in vacancies:
            if v.key_skills:
                for skill in v.key_skills:
                    skills_counter[skill.name] += 1
                    skills_by_vacancy[skill.name].append(v.id)
        
        top_skills = skills_counter.most_common(top_n)
        
        total_vacancies = len(vacancies)
        
        result = {
            "total_skills": len(skills_counter),
            "top_skills": [
                {
                    "name": name,
                    "count": count,
                    "percentage": round(count / total_vacancies * 100, 1),
                }
                for name, count in top_skills
            ],
            "all_skills": dict(skills_counter.most_common()),
        }
        
        return result
    
    def analyze_areas(self, vacancies: list[VacancyBase]) -> dict:
        """
        Анализирует распределение по регионам.
        
        Args:
            vacancies: Список вакансий
            
        Returns:
            dict с регионами
        """
        areas_counter = Counter()
        
        for v in vacancies:
            if v.area:
                areas_counter[v.area.name] += 1
        
        total = len(vacancies)
        
        return {
            "total_areas": len(areas_counter),
            "top_areas": [
                {
                    "name": name,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for name, count in areas_counter.most_common(10)
            ],
        }
    
    def analyze_experience(self, vacancies: list[VacancyBase]) -> dict:
        """
        Анализирует требования к опыту.
        
        Args:
            vacancies: Список вакансий
            
        Returns:
            dict с опытом
        """
        exp_counter = Counter()
        
        for v in vacancies:
            if v.experience:
                exp_counter[v.experience.name] += 1
        
        total = len(vacancies)
        
        return {
            "experience_requirements": [
                {
                    "name": name,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for name, count in exp_counter.most_common()
            ],
        }
    
    def analyze_employment(self, vacancies: list[VacancyBase]) -> dict:
        """
        Анализирует типы занятости.
        
        Args:
            vacancies: Список вакансий
            
        Returns:
            dict с типами занятости
        """
        emp_counter = Counter()
        
        for v in vacancies:
            if v.employment:
                emp_counter[v.employment.name] += 1
        
        total = len(vacancies)
        
        return {
            "employment_types": [
                {
                    "name": name,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
                for name, count in emp_counter.most_common()
            ],
        }
    
    def generate_report(
        self,
        vacancies: list[VacancyDetail],
        search_query: str = "",
    ) -> str:
        """
        Генерирует текстовый отчёт по рынку.
        
        Args:
            vacancies: Список вакансий
            search_query: Поисковый запрос
            
        Returns:
            Строка с отчётом
        """
        if not vacancies:
            return "❌ Нет данных для анализа"
        
        lines = [
            f"📊 Анализ рынка труда",
            f"{'='*50}",
            f"🔍 Запрос: {search_query or 'Не указан'}",
            f"📈 Найдено вакансий: {len(vacancies)}",
            f"",
        ]
        
        # Зарплаты
        salary_stats = self.analyze_salaries(vacancies)
        if "error" not in salary_stats:
            lines.append("💰 Зарплаты:")
            if "avg_from" in salary_stats:
                lines.append(f"   Средняя (от): {salary_stats['avg_from']:,} ₽")
            if "avg_to" in salary_stats:
                lines.append(f"   Средняя (до): {salary_stats['avg_to']:,} ₽")
            if "median_from" in salary_stats:
                lines.append(f"   Медиана (от): {salary_stats['median_from']:,} ₽")
            lines.append("")
        
        # Навыки
        skills_stats = self.analyze_skills(vacancies, top_n=10)
        if skills_stats.get("top_skills"):
            lines.append("🔧 Топ-10 востребованных навыков:")
            for i, skill in enumerate(skills_stats["top_skills"], 1):
                lines.append(f"   {i}. {skill['name']} — {skill['percentage']}%")
            lines.append("")
        
        # Регионы
        area_stats = self.analyze_areas(vacancies)
        if area_stats.get("top_areas"):
            lines.append("📍 Топ регионов:")
            for i, area in enumerate(area_stats["top_areas"][:5], 1):
                lines.append(f"   {i}. {area['name']} — {area['count']} вакансий")
            lines.append("")
        
        # Опыт
        exp_stats = self.analyze_experience(vacancies)
        if exp_stats.get("experience_requirements"):
            lines.append("💼 Требования к опыту:")
            for exp in exp_stats["experience_requirements"]:
                lines.append(f"   • {exp['name']} — {exp['percentage']}%")
        
        return "\n".join(lines)
    
    def format_salary_chart(self, salary_stats: dict) -> str:
        """
        Форматирует ASCII-график зарплат.
        
        Args:
            salary_stats: Статистика зарплат
            
        Returns:
            ASCII-график
        """
        if "avg_from" not in salary_stats or "avg_to" not in salary_stats:
            return "Нет данных для графика"
        
        avg_from = salary_stats["avg_from"]
        avg_to = salary_stats["avg_to"]
        
        # Простой ASCII бар
        max_val = avg_to
        bar_length = 30
        
        from_bar = int((avg_from / max_val) * bar_length)
        to_bar = int((avg_to / max_val) * bar_length)
        
        chart = [
            "💰 Зарплатный диапазон:",
            "",
            f"   от: {avg_from:,} ₽ {'█' * from_bar}{'░' * (bar_length - from_bar)}",
            f"   до: {avg_to:,} ₽ {'█' * to_bar}{'░' * (bar_length - to_bar)}",
        ]
        
        return "\n".join(chart)
