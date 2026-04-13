"""
URL эндпоинты HH.ru API.

Полный список эндпоинтов для работы с вакансиями, резюме,
откликами, справочниками и аналитикой.

Документация: https://github.com/hhru/api
"""

# === Базовый URL ===
BASE_URL = "https://api.hh.ru"

# === OAuth 2.0 ===
OAUTH_AUTHORIZE = "https://hh.ru/oauth/authorize"
OAUTH_TOKEN = f"{BASE_URL}/token"

# === Вакансии (публичные) ===
# Поиск вакансий
VACANCIES_SEARCH = f"{BASE_URL}/vacancies"

# Детали вакансии
VACANCY_DETAIL = f"{BASE_URL}/vacancies/{{vacancy_id}}"

# Похожие вакансии
VACANCY_SIMILAR = f"{BASE_URL}/vacancies/{{vacancy_id}}/similar_vacancies"

# Статистика вакансии
VACANCY_STATISTICS = f"{BASE_URL}/vacancies/{{vacancy_id}}/statistics"

# Просмотры вакансии
VACANCY_VIEWS = f"{BASE_URL}/vacancies/{{vacancy_id}}/views"

# === Вакансии (от имени работодателя) ===
# Управление вакансиями
VACANCIES_MANAGE = f"{BASE_URL}/vacancies/managed"
VACANCY_CREATE = f"{BASE_URL}/vacancies"
VACANCY_UPDATE = f"{BASE_URL}/vacancies/{{vacancy_id}}"
VACANCY_ARCHIVE = f"{BASE_URL}/vacancies/{{vacancy_id}}/archive"
VACANCY_UNARCHIVE = f"{BASE_URL}/vacancies/{{vacancy_id}}/open"
VACANCY_DELETE = f"{BASE_URL}/vacancies/{{vacancy_id}}"

# Черновики вакансий
VACANCY_DRAFTS = f"{BASE_URL}/vacancies/drafts"
VACANCY_DRAFT_CREATE = f"{BASE_URL}/vacancies/drafts"
VACANCY_DRAFT_DETAIL = f"{BASE_URL}/vacancies/drafts/{{draft_id}}"
VACANCY_DRAFT_UPDATE = f"{BASE_URL}/vacancies/drafts/{{draft_id}}"
VACANCY_DRAFT_DELETE = f"{BASE_URL}/vacancies/drafts/{{draft_id}}"

# === Отклики и переговоры ===
# История откликов (переговоры)
NEGOTIATIONS = f"{BASE_URL}/negotiations"
NEGOTIATIONS_ACTIVE = f"{BASE_URL}/negotiations/active"
NEGOTIATIONS_VACANCY = f"{BASE_URL}/negotiations/vacancies"
NEGOTIATIONS_RESUME = f"{BASE_URL}/negotiations/resumes"
NEGOTIATIONS_DETAIL = f"{BASE_URL}/negotiations/{{vacancy_id}}/{{resume_id}}"

# Отклик на вакансию
NEGOTIATIONS_APPLY = f"{BASE_URL}/negotiations"

# Изменение статуса отклика
NEGOTIATIONS_STATUS = f"{BASE_URL}/negotiations/{{vacancy_id}}/{{resume_id}}"

# Приглашение на вакансию
NEGOTIATIONS_INVITE = f"{BASE_URL}/negotiations/{{vacancy_id}}/invitations"

# === Резюме (соискатель) ===
# Список своих резюме
RESUMES_MINE = f"{BASE_URL}/resumes/mine"

# Детали резюме
RESUME_DETAIL = f"{BASE_URL}/resumes/{{resume_id}}"

# Создание/обновление резюме
RESUME_CREATE = f"{BASE_URL}/resumes"
RESUME_UPDATE = f"{BASE_URL}/resumes/{{resume_id}}"
RESUME_DELETE = f"{BASE_URL}/resumes/{{resume_id}}"

# Экспорт резюме
RESUME_EXPORT = f"{BASE_URL}/resumes/{{resume_id}}/export"

# Статистика просмотров резюме
RESUME_STATISTICS = f"{BASE_URL}/resumes/{{resume_id}}/statistics"
RESUME_VIEWS = f"{BASE_URL}/resumes/{{resume_id}}/views"

# === Компании ===
# Информация о компании
COMPANY_DETAIL = f"{BASE_URL}/employers/{{employer_id}}"

# Вакансии компании
COMPANY_VACANCIES = f"{BASE_URL}/employers/{{employer_id}}/vacancies"

# Информация о работодателе (из отклика)
EMPLOYER_MANAGERS = f"{BASE_URL}/employers/{{employer_id}}/managers"

# === Справочники ===
# Регионы
AREAS = f"{BASE_URL}/areas"
AREA_DETAIL = f"{BASE_URL}/areas/{{area_id}}"

# Метро
METRO_STATIONS = f"{BASE_URL}/areas/{{area_id}}/metro"
METRO_LINES = f"{BASE_URL}/areas/{{area_id}}/metro/lines"

# Профессии (рубрики)
PROFESSIONAL_ROLES = f"{BASE_URL}/professional_roles"

# Отрасли компании
INDUSTRIES = f"{BASE_URL}/industries"

# Языки
LANGUAGES = f"{BASE_URL}/languages"

# ВУЗы
UNIVERSITIES = f"{BASE_URL}/universities"

# Ключевые навыки
SKILLS = f"{BASE_URL}/skills"

# Зарплатные справочники
SALARY_STATISTICS = f"{BASE_URL}/statistics/salaries"
SALARY_BY_SPECIALIZATION = f"{BASE_URL}/statistics/salaries_by_specialization"

# === Поиск подсказок (Autosuggest) ===
SUGGEST_VACANCY = f"{BASE_URL}/suggests/vacancy_positions"
SUGGEST_COMPANY = f"{BASE_URL}/suggests/employers"
SUGGEST_UNIVERSITY = f"{BASE_URL}/suggests/universities"

# === Специальные эндпоинты ===
# Информация о приложении
APP_INFO = f"{BASE_URL}/app/info"

# Информация о пользователе
USER_INFO = f"{BASE_URL}/me"

# Платные услуги
SERVICES = f"{BASE_URL}/services"

# Менеджеры работодателя
MANAGER_INFO = f"{BASE_URL}/manager/info"
MANAGER_CHECK_LIMIT = f"{BASE_URL}/manager/check_limit"

# Webhooks
WEBHOOKS = f"{BASE_URL}/webhooks"
WEBHOOK_DETAIL = f"{BASE_URL}/webhooks/{{webhook_id}}"

# === Динамические эндпоинты (с параметрами) ===
def get_vacancy_url(vacancy_id: str) -> str:
    """Получить URL детали вакансии."""
    return VACANCY_DETAIL.format(vacancy_id=vacancy_id)

def get_similar_url(vacancy_id: str) -> str:
    """Получить URL похожих вакансий."""
    return VACANCY_SIMILAR.format(vacancy_id=vacancy_id)

def get_negotiation_url(vacancy_id: str, resume_id: str) -> str:
    """Получить URL переговоров."""
    return NEGOTIATIONS_DETAIL.format(vacancy_id=vacancy_id, resume_id=resume_id)

def get_resume_url(resume_id: str) -> str:
    """Получить URL резюме."""
    return RESUME_DETAIL.format(resume_id=resume_id)

def get_company_url(employer_id: str) -> str:
    """Получить URL компании."""
    return COMPANY_DETAIL.format(employer_id=employer_id)

def get_area_url(area_id: str) -> str:
    """Получить URL региона."""
    return AREA_DETAIL.format(area_id=area_id)
