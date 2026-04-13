"""
Конфигурация приложения HH.ru MCP Server.

Загружает переменные окружения и предоставляет настройки
для API клиента, OAuth и AI-фич.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Базовый путь проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# === HH.RU API Configuration ===
HH_API_BASE_URL = "https://api.hh.ru"
HH_DEV_BASE_URL = "https://api.hh.ru"

# OAuth 2.0
HH_CLIENT_ID = os.getenv("HH_CLIENT_ID", "")
HH_CLIENT_SECRET = os.getenv("HH_CLIENT_SECRET", "")
HH_REDIRECT_URI = os.getenv("HH_REDIRECT_URI", "https://localhost/callback")
HH_ACCESS_TOKEN = os.getenv("HH_ACCESS_TOKEN", "")
HH_REFRESH_TOKEN = os.getenv("HH_REFRESH_TOKEN", "")

# User-Agent (обязателен для hh.ru API)
HH_USER_AGENT = os.getenv("HH_USER_AGENT", "HH MCP Server/1.0 (your_email@example.com)")

# App Token (для авторизации приложения)
HH_APP_TOKEN = os.getenv("HH_APP_TOKEN", "")

# === Rate Limiting ===
# hh.ru ограничивает запросы: ~100/мин для анонимных, ~200/мин для авторизованных
RATE_LIMIT_REQUESTS = int(os.getenv("HH_RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_PERIOD = int(os.getenv("HH_RATE_LIMIT_PERIOD", "60"))

# === Cache Configuration ===
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL", "300"))  # 5 минут по умолчанию
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

# === AI Configuration ===
# Для AI-скоринга и генерации писем
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# Скоринг
SCORING_MIN = 0
SCORING_MAX = 100
SCORING_THRESHOLD = int(os.getenv("SCORING_THRESHOLD", "60"))  # Минимальный порог релевантности

# Веса для скоринга
SCORING_WEIGHTS = {
    "skills_match": 0.35,      # Совпадение навыков
    "salary_match": 0.20,      # Соответствие зарплате
    "location_match": 0.15,    # Локация
    "experience_match": 0.15,  # Опыт работы
    "employment_match": 0.10,  # Тип занятости
    "company_rating": 0.05,    # Рейтинг компании
}

# === Monitoring Configuration ===
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL", "300"))  # 5 минут
MONITOR_ENABLED = os.getenv("MONITOR_ENABLED", "true").lower() == "true"

# Уведомления
NOTIFY_CONSOLE = True
NOTIFY_TELEGRAM = os.getenv("NOTIFY_TELEGRAM", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "hh_mcp.log"))

# === Application Settings ===
APP_NAME = "HH.ru MCP Server"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered MCP server for HH.ru job search and application management"
