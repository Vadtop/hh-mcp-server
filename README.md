# HH.ru MCP Server

MCP сервер для автоматизации поиска работы на hh.ru через Playwright.

Работает как инструмент для AI-ассистентов (Cline, Claude, Cursor) — 19 MCP инструментов для поиска вакансий, управления резюме и автооткликов.

> Почему Playwright а не API? С декабря 2025 hh.ru закрыл API для соискателей. Решение — эмуляция браузера.

## Что умеет

- Поиск вакансий по всей России (включая удалёнку)
- Просмотр деталей вакансий и информации о компаниях
- Управление резюме
- Автоотклики с сопроводительным письмом
- AI скоринг релевантности вакансий (0-100)
- Аналитика рынка труда
- Мониторинг статусов откликов
- Карьерный советник + анализ пробелов в навыках

## Стек

Python · FastMCP · Playwright · Pydantic · scikit-learn · OpenAI

## Быстрый старт

```bash
pip install -r requirements.txt
playwright install chromium

# Авторизация hh.ru (один раз)
python auth_once.py

# Запуск MCP сервера
python run_mcp.py
```

## Подключение к Cline (VS Code)

Добавить в `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "hh-mcp": {
      "command": "python",
      "args": ["path/to/hh_mcp_server_v2/run_mcp.py"]
    }
  }
}
```

После подключения — просто пишешь в чат:

```
Найди удалённые вакансии AI интегратор, зарплата от 100к
```

## MCP инструменты (19)

| Инструмент | Описание |
|---|---|
| `hh_search` | Поиск вакансий (text, salary, remote) |
| `hh_get_vacancy` | Детали вакансии по ID |
| `hh_get_employer` | Информация о компании |
| `hh_apply_vacancy` | Отклик с сопроводительным письмом |
| `hh_get_applications` | История откликов и статусы |
| `hh_get_my_resumes` | Мои резюме |
| `hh_score_vacancy` | AI скоринг релевантности 0-100 |
| `hh_generate_letter` | Генерация сопроводительного письма |
| `hh_market_analytics` | Аналитика рынка труда |
| `hh_career_advisor` | Карьерный советник |
| `hh_skills_gap` | Анализ пробелов в навыках |
| `hh_salary_forecast` | Прогноз зарплаты по навыкам |
| ... | + 7 других инструментов |

## Автор

[Vadim Titov](https://github.com/Vadtop) · Telegram: @vadimka163
