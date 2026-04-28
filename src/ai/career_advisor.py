"""
AI Карьерный советник.

Реализует:
- Анализ пробелов в навыках (Skills Gap)
- Оптимизация резюме
- Прогноз зарплаты
- Рекомендации по обучению
"""

import logging
from typing import Optional
from collections import Counter

from src.models.vacancy import VacancyDetail
from src.models.resume import ResumeDetail

logger = logging.getLogger(__name__)


class CareerAdvisor:
    """
    AI-powered карьерный советник.
    
    Анализирует резюме vs вакансии и даёт рекомендации:
    - Чего не хватает
    - Что изучить
    - Как улучшить резюме
    - Какой будет зарплата
    """
    
    def __init__(self):
        # Карта навыков и примерных зарплатных бонусов
        self.skill_salary_bonuses = {
            "llm": 50000, "rag": 40000, "agents": 45000, "mcp": 35000,
            "vector db": 30000, "langgraph": 25000, "pytorch": 35000,
            "kubernetes": 35000, "docker": 25000, "system design": 50000,
            "microservices": 35000, "aws": 40000, "ci/cd": 25000,
            "terraform": 30000, "kafka": 30000, "redis": 20000,
            "postgresql": 20000, "mongodb": 20000, "grpc": 20000,
            "graphql": 15000, "react": 25000, "typescript": 20000,
            "golang": 35000, "rust": 40000, "machine learning": 45000,
            "devops": 35000, "mlops": 45000, "spark": 30000,
        }
        
        # Рекомендации по обучению
        self.learning_recommendations = {
            "llm": "LLM Engineering: LangChain, prompt engineering, fine-tuning (2-3 месяца)",
            "rag": "RAG-системы: векторные БД, реранкеры, guardrails (1-2 месяца)",
            "agents": "AI Agents: LangGraph, CrewAI, AutoGen (2-3 месяца)",
            "mcp": "MCP-протокол: FastMCP 2.x, tool integration (2 недели)",
            "vector db": "Векторные БД: ChromaDB, Qdrant, Pinecone (2 недели)",
            "langgraph": "LangGraph: stateful agents, DAG workflows (3 недели)",
            "pytorch": "PyTorch: нейросети, fine-tuning, LoRA (2-3 месяца)",
            "kubernetes": "Изучить K8s: курсы Kubernetes Certified Administrator (3-4 недели)",
            "docker": "Освоить Docker: контейнеризация, docker-compose (2 недели)",
            "system design": "Прочитать 'Designing Data-Intensive Applications' (2-3 месяца)",
            "microservices": "Практика микросервисов: API Gateway, Service Discovery (1-2 месяца)",
            "aws": "AWS Certified Solutions Architect (2-3 месяца)",
            "ci/cd": "Настроить CI/CD pipeline: GitHub Actions, GitLab CI (1-2 недели)",
            "terraform": "Infrastructure as Code: Terraform курс (2 недели)",
            "kafka": "Apache Kafka: основы и продвинутый уровень (3-4 недели)",
            "redis": "Redis: кэширование, очереди (1-2 недели)",
            "postgresql": "PostgreSQL: оптимизация запросов, индексы (2 недели)",
            "mongodb": "MongoDB: документо-ориентированная БД (2 недели)",
            "grpc": "gRPC для микросервисов (2 недели)",
            "graphql": "GraphQL API (1-2 недели)",
            "react": "React + Next.js (1-2 месяца)",
            "typescript": "TypeScript для продвинутых (2-3 недели)",
            "golang": "Go: конкурентность, микросервисы (2-3 месяца)",
            "rust": "Rust: ownership, async (3-4 месяца)",
            "machine learning": "ML: Python, scikit-learn, TensorFlow (3-6 месяцев)",
            "devops": "DevOps практика: CI/CD + K8s + мониторинг (2-3 месяца)",
            "mlops": "MLOps: модельный деплой, мониторинг, feature store (2-3 месяца)",
            "spark": "Apache Spark: distributed data processing (3-4 недели)",
        }
    
    def analyze_skills_gap(
        self,
        resume: ResumeDetail,
        target_vacancies: list[VacancyDetail],
    ) -> dict:
        """
        Анализирует пробелы в навыках между резюме и целевыми вакансиями.
        
        Args:
            resume: Резюме пользователя
            target_vacancies: Целевые вакансии
            
        Returns:
            dict с анализом пробелов
        """
        resume_skills = set(s.lower() for s in resume.skills_flat_list)
        
        # Собираем все требуемые навыки из вакансий
        all_required_skills = Counter()
        for v in target_vacancies:
            if v.key_skills:
                for skill in v.key_skills:
                    all_required_skills[skill.name.lower()] += 1
        
        total_vacancies = len(target_vacancies)
        
        # Определяем пробелы
        missing_skills = []
        matched_skills = []
        
        for skill, count in all_required_skills.most_common():
            percentage = count / total_vacancies * 100
            
            if skill in resume_skills:
                matched_skills.append({
                    "skill": skill,
                    "demand": count,
                    "percentage": round(percentage, 1),
                })
            else:
                bonus = self.skill_salary_bonuses.get(skill, 0)
                learning = self.learning_recommendations.get(skill, "")
                
                missing_skills.append({
                    "skill": skill,
                    "demand": count,
                    "percentage": round(percentage, 1),
                    "estimated_bonus": bonus,
                    "learning": learning,
                })
        
        # Общий скоринг совпадения
        total_required = len(all_required_skills)
        matched_count = len(matched_skills)
        match_percentage = (matched_count / total_required * 100) if total_required > 0 else 0
        
        return {
            "total_required_skills": total_required,
            "matched_skills": matched_count,
            "missing_skills": len(missing_skills),
            "match_percentage": round(match_percentage, 1),
            "matched": matched_skills[:10],  # Топ-10 совпавших
            "missing": missing_skills[:15],  # Топ-15 недостающих
            "critical_gaps": [s for s in missing_skills if s["percentage"] >= 60][:5],
        }
    
    def generate_learning_roadmap(
        self,
        skills_gap: dict,
        timeline_months: int = 12,
    ) -> str:
        """
        Генерирует дорожную карту обучения.
        
        Args:
            skills_gap: Результат анализа пробелов
            timeline_months: Таймлайн в месяцах
            
        Returns:
            Строка с дорожной картой
        """
        missing = skills_gap.get("missing", [])
        
        if not missing:
            return "🎉 Отлично! У вас уже есть все требуемые навыки!"
        
        lines = [
            "📚 Дорожная карта обучения:",
            f"{'='*50}",
            f"📅 Таймлайн: {timeline_months} месяцев",
            f"🎯 Навыков для изучения: {len(missing)}",
            "",
        ]
        
        # Сортируем по востребованности
        sorted_skills = sorted(missing, key=lambda x: x["percentage"], reverse=True)
        
        # Распределяем по времени
        total_months = timeline_months
        items_per_month = max(1, len(sorted_skills) // total_months)
        
        current_month = 1
        for i, skill_info in enumerate(sorted_skills[:12], 1):  # Макс 12 навыков
            month = (i - 1) // max(1, items_per_month) + 1
            
            if month == current_month:
                lines.append(f"📆 Месяц {month}:")
                current_month = month + 1
            
            bonus = skill_info.get("estimated_bonus", 0)
            lines.append(f"   • {skill_info['skill'].title()}")
            lines.append(f"     Востребованность: {skill_info['percentage']}%")
            if bonus:
                lines.append(f"     Бонус к зарплате: +{bonus:,} ₽")
            if skill_info.get("learning"):
                lines.append(f"     {skill_info['learning']}")
            lines.append("")
        
        # Итоговый бонус
        total_bonus = sum(s.get("estimated_bonus", 0) for s in sorted_skills[:5])
        if total_bonus:
            lines.append(f"💰 Потенциальный бонус к зарплате: +{total_bonus:,} ₽")
        
        return "\n".join(lines)
    
    def generate_resume_suggestions(
        self,
        resume: ResumeDetail,
        skills_gap: dict,
    ) -> dict:
        """
        Генерирует рекомендации по улучшению резюме.
        
        Args:
            resume: Резюме
            skills_gap: Результат анализа пробелов
            
        Returns:
            dict с рекомендациями
        """
        suggestions = {
            "add_skills": [],
            "improve_descriptions": [],
            "add_metrics": [],
            "add_projects": [],
            "general": [],
        }
        
        # Предлагает добавить недостающие навыки
        missing = skills_gap.get("missing", [])
        critical = skills_gap.get("critical_gaps", [])
        
        for skill in critical:
            suggestions["add_skills"].append({
                "skill": skill["skill"],
                "reason": f"Требуется в {skill['percentage']}% вакансий",
                "action": f"Добавить после изучения: {skill.get('learning', '')}",
            })
        
        # Предлагает улучшить описания
        if resume.about and len(resume.about) < 200:
            suggestions["improve_descriptions"].append(
                "Раздел 'О себе' слишком короткий. Добавьте больше деталей о вашем опыте и достижениях."
            )
        
        # Предлагает добавить метрики
        if resume.experience:
            for exp in resume.experience:
                if exp.description and len(exp.description) < 100:
                    suggestions["add_metrics"].append(
                        f"В опыте '{exp.position}' добавьте конкретные достижения и метрики "
                        f"(например: 'увеличил производительность на 30%', 'обработал 1000+ RPS')"
                    )
        
        # Предлагает добавить проекты
        if not resume.projects or len(resume.projects) < 2:
            suggestions["add_projects"].append(
                "Добавьте 2-3 pet-проекта на GitHub, чтобы показать практические навыки"
            )
        
        # Общие рекомендации
        if not resume.skills or len(resume.skills) < 5:
            suggestions["general"].append(
                "Добавьте хотя бы 5-10 ключевых навыков для лучшего匹配 с вакансиями"
            )
        
        return suggestions
    
    def forecast_salary(
        self,
        current_salary: Optional[int],
        current_skills: list[str],
        target_skills: list[str],
        timeline_months: int = 12,
    ) -> dict:
        """
        Прогнозирует зарплату после изучения новых навыков.
        
        Args:
            current_salary: Текущая зарплата
            current_skills: Текущие навыки
            target_skills: Навыки для изучения
            timeline_months: Таймлайн
            
        Returns:
            dict с прогнозом
        """
        if not current_salary:
            return {"error": "Укажите текущую зарплату"}
        
        # Рассчитываем бонусы
        potential_bonus = 0
        milestones = []
        
        for i, skill in enumerate(target_skills[:6], 1):
            skill_lower = skill.lower()
            bonus = self.skill_salary_bonuses.get(skill_lower, 0)
            
            if bonus:
                potential_bonus += bonus
                
                # Распределяем по времени
                month = (i * timeline_months) // 6
                
                milestones.append({
                    "skill": skill,
                    "month": month,
                    "bonus": bonus,
                    "new_salary": current_salary + potential_bonus,
                })
        
        # Итоговый прогноз
        final_salary = current_salary + potential_bonus
        
        return {
            "current_salary": current_salary,
            "potential_bonus": potential_bonus,
            "forecast_salary": final_salary,
            "growth_percentage": round((potential_bonus / current_salary) * 100, 1),
            "timeline_months": timeline_months,
            "milestones": milestones,
        }
    
    def format_advisor_report(
        self,
        resume: ResumeDetail,
        skills_gap: dict,
        roadmap: str,
        suggestions: dict,
        salary_forecast: Optional[dict] = None,
    ) -> str:
        """
        Форматирует полный отчёт советника.
        
        Args:
            resume: Резюме
            skills_gap: Анализ пробелов
            roadmap: Дорожная карта
            suggestions: Рекомендации
            salary_forecast: Прогноз зарплаты
            
        Returns:
            Полный отчёт
        """
        lines = [
            "🎯 AI Карьерный советник",
            f"{'='*60}",
            "",
            f"👤 {resume.full_name}",
            f"💼 {resume.title or 'Не указана'}",
            f"📅 Опыт: {resume.total_experience_formatted}",
            f"",
        ]
        
        # Skills gap
        lines.append(f"📊 Анализ навыков:")
        lines.append(f"   Совпадение: {skills_gap.get('match_percentage', 0)}%")
        lines.append(f"   Навыков есть: {skills_gap.get('matched_skills', 0)}")
        lines.append(f"   Навыков не хватает: {skills_gap.get('missing_skills', 0)}")
        lines.append("")
        
        # Критические пробелы
        critical = skills_gap.get("critical_gaps", [])
        if critical:
            lines.append("⚠️ Критические пробелы (требуются в 60%+ вакансий):")
            for gap in critical:
                lines.append(f"   • {gap['skill'].title()} ({gap['percentage']}%)")
            lines.append("")
        
        # Дорожная карта
        lines.append(roadmap)
        lines.append("")
        
        # Рекомендации
        if suggestions.get("add_skills"):
            lines.append("🔧 Добавить навыки:")
            for s in suggestions["add_skills"][:5]:
                lines.append(f"   • {s['skill']} — {s['reason']}")
            lines.append("")
        
        if suggestions.get("add_metrics"):
            lines.append("📈 Добавить метрики:")
            for m in suggestions["add_metrics"][:3]:
                lines.append(f"   • {m}")
            lines.append("")
        
        # Прогноз зарплаты
        if salary_forecast and "error" not in salary_forecast:
            lines.append(f"💰 Прогноз зарплаты:")
            lines.append(f"   Текущая: {salary_forecast['current_salary']:,} ₽")
            lines.append(f"   Потенциальная: {salary_forecast['forecast_salary']:,} ₽")
            lines.append(f"   Рост: +{salary_forecast['growth_percentage']}%")
        
        return "\n".join(lines)
