"""
AI-модуль для скоринга вакансий.

Реализует расширенный скоринг с использованием:
- TF-IDF для анализа текста
- Семантического подобия
- Весовых коэффициентов
- Персонализации на основе резюме
"""

import re
from typing import Optional
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models.vacancy import VacancyDetail, VacancyScored
from src.config import SCORING_WEIGHTS


class AIVacancyScorer:
    """
    AI-скоринг вакансий с использованием TF-IDF.
    
    Оценивает релевантность вакансии на основе:
    - Совпадения навыков (TF-IDF)
    - Описания вакансии vs резюме
    - Зарплатных ожиданий
    - Локации
    - Опыта работы
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=1000,
        )
    
    def score_with_resume(
        self,
        vacancy: VacancyDetail,
        resume_text: str,
        resume_skills: list[str],
        expected_salary: Optional[int] = None,
        preferred_area: Optional[str] = None,
    ) -> VacancyScored:
        """
        Оценивает вакансию на основе резюме.
        
        Args:
            vacancy: Вакансия
            resume_text: Текст резюме
            resume_skills: Навыки из резюме
            expected_salary: Ожидаемая зарплата
            preferred_area: Предпочтительный регион
            
        Returns:
            VacancyScored с оценкой
        """
        # Конвертируем в VacancyScored
        scored = VacancyScored(**vacancy.model_dump())
        
        # 1. TF-IDF скоринг описания вакансии vs резюме
        tfidf_score = self._calculate_tfidf_similarity(resume_text, vacancy.description_plain)
        
        # 2. Скоринг навыков
        skills_score = self._calculate_skills_score(resume_skills, vacancy.skills_list)
        
        # 3. Скоринг зарплаты
        salary_score = self._calculate_salary_score(
            expected_salary,
            vacancy.salary.from_amount if vacancy.salary else None,
            vacancy.salary.to_amount if vacancy.salary else None,
        )
        
        # 4. Скоринг локации
        location_score = self._calculate_location_score(
            preferred_area,
            vacancy.area.id if vacancy.area else None,
        )
        
        # 5. Бонус за релевантность опыта
        experience_bonus = self._calculate_experience_bonus(vacancy)
        
        # Итоговый скоринг с весами
        total = (
            tfidf_score * 0.30 +
            skills_score * SCORING_WEIGHTS["skills_match"] +
            salary_score * SCORING_WEIGHTS["salary_match"] +
            location_score * SCORING_WEIGHTS["location_match"] +
            experience_bonus * 0.10
        )
        
        # Нормализуем в 0-100
        final_score = min(100, max(0, int(total)))
        
        scored.score = final_score
        scored.score_details = {
            "tfidf_similarity": round(tfidf_score, 1),
            "skills_match": round(skills_score, 1),
            "salary_match": round(salary_score, 1),
            "location_match": round(location_score, 1),
            "experience_bonus": round(experience_bonus, 1),
        }
        scored.score_comment = self._interpret_score(final_score)
        
        return scored
    
    def batch_score(
        self,
        vacancies: list[VacancyDetail],
        resume_text: str,
        resume_skills: list[str],
        expected_salary: Optional[int] = None,
        preferred_area: Optional[str] = None,
    ) -> list[VacancyScored]:
        """
        Оценивает пакет вакансий и сортирует по релевантности.
        
        Args:
            vacancies: Список вакансий
            resume_text: Текст резюме
            resume_skills: Навыки из резюме
            expected_salary: Ожидаемая зарплата
            preferred_area: Предпочтительный регион
            
        Returns:
            list[VacancyScored] отсортированный по score
        """
        scored_vacancies = []
        
        for vacancy in vacancies:
            scored = self.score_with_resume(
                vacancy=vacancy,
                resume_text=resume_text,
                resume_skills=resume_skills,
                expected_salary=expected_salary,
                preferred_area=preferred_area,
            )
            scored_vacancies.append(scored)
        
        # Сортируем по score (по убыванию)
        return sorted(scored_vacancies, key=lambda v: v.score, reverse=True)
    
    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Рассчитывает TF-IDF подобие двух текстов.
        
        Args:
            text1: Текст 1 (резюме)
            text2: Текст 2 (вакансия)
            
        Returns:
            Score 0-100
        """
        if not text1 or not text2:
            return 50.0
        
        try:
            # TF-IDF векторизация
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            
            # Косинусное подобие
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Нормализуем в 0-100
            return similarity * 100
            
        except Exception:
            return 50.0
    
    def _calculate_skills_score(
        self,
        resume_skills: list[str],
        vacancy_skills: list[str],
    ) -> float:
        """
        Рассчитывает скоринг навыков.
        
        Args:
            resume_skills: Навыки из резюме
            vacancy_skills: Навыки из вакансии
            
        Returns:
            Score 0-100
        """
        if not resume_skills or not vacancy_skills:
            return 50.0
        
        # Нормализуем
        set1 = set(self._normalize_skill(s) for s in resume_skills)
        set2 = set(self._normalize_skill(s) for s in vacancy_skills)
        
        # Intersection
        matched = set1 & set2
        
        # Precision: сколько из требуемых есть у нас
        precision = len(matched) / len(set2) if set2 else 0
        
        # Recall: сколько из наших используется
        recall = len(matched) / len(set1) if set1 else 0
        
        # F1 score
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0
        
        return f1 * 100
    
    def _calculate_salary_score(
        self,
        expected: Optional[int],
        from_amount: Optional[int],
        to_amount: Optional[int],
    ) -> float:
        """Рассчитывает скоринг зарплаты."""
        if not expected or (not from_amount and not to_amount):
            return 50.0
        
        if from_amount and to_amount:
            if from_amount <= expected <= to_amount:
                return 100.0
            elif expected < from_amount:
                return 80.0  # Ожидаем меньше — нормально
            else:
                # Ожидаем больше
                diff = (expected - to_amount) / to_amount
                return max(20, 80 - diff * 100)
        
        elif from_amount:
            if expected <= from_amount:
                return 90.0
            else:
                diff = (expected - from_amount) / from_amount
                return max(20, 70 - diff * 100)
        
        elif to_amount:
            if expected <= to_amount:
                return 100.0
            else:
                diff = (expected - to_amount) / to_amount
                return max(20, 60 - diff * 100)
        
        return 50.0
    
    def _calculate_location_score(
        self,
        preferred: Optional[str],
        actual: Optional[str],
    ) -> float:
        """Рассчитывает скоринг локации."""
        if not preferred or not actual:
            return 50.0
        
        return 100.0 if preferred == actual else 30.0
    
    def _calculate_experience_bonus(self, vacancy: VacancyDetail) -> float:
        """Рассчитывает бонус за релевантность опыта."""
        # Если вакансия не требует опыта — бонус
        if vacancy.experience and vacancy.experience.id == "noExperience":
            return 80.0
        
        # Если требует senior — чуть меньше (сложнее)
        if vacancy.experience and vacancy.experience.id == "moreThan6":
            return 60.0
        
        return 70.0  # Middle
    
    def _normalize_skill(self, skill: str) -> str:
        """Нормализует навык."""
        return skill.lower().strip().replace("-", " ").replace("_", " ")
    
    def _interpret_score(self, score: int) -> str:
        """Интерпретирует скоринг."""
        if score >= 90:
            return "🎯 Отличное совпадение! Стоит откликнуться!"
        elif score >= 75:
            return "✅ Хорошее совпадение. Рекомендуется отклик."
        elif score >= 60:
            return "👍 Среднее совпадение. Можно попробовать."
        elif score >= 40:
            return "⚠️ Низкое совпадение. Проверьте требования."
        else:
            return "❌ Слабое совпадение. Вероятно не подходит."
