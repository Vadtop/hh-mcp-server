# HH MCP Server v2 — Контекст проекта

## 📍 Текущий статус (13 апреля 2026)
- **MCP сервер**: настроен в `.qwen/settings.json`, 19 инструментов
- **Веб-дашборд**: FastAPI на http://127.0.0.1:8000
- **Авторизация**: через телефон + SMS (сессия в `.browser_session/`)
- **Парсинг**: Playwright + fallback селекторы

## 🎯 Цель проекта
MCP сервер для hh.ru — AI-ассистент для поиска вакансий, управления резюме, автооткликов, AI-скоринга и мониторинга через hh.ru API + Playwright.

## 📁 Структура проекта
```
hh_mcp_server_v2/
├── src/
│   ├── main.py           # MCP сервер (FastMCP, 19 tools)
│   ├── web_app.py        # Веб-дашборд (FastAPI)
│   ├── config.py         # Конфигурация
│   ├── browser/          # Playwright движок, авторизация, парсеры
│   ├── services/         # Сервисы: вакансии, резюме, отклики
│   ├── ai/               # AI: скоринг, письма, карьерный советник
│   └── models/           # Pydantic модели
├── .browser_session/     # Сохранённая сессия браузера
├── requirements.txt      # Зависимости
└── .env.example          # Переменные окружения
```

## 🔧 MCP инструменты (19 штук)
### Вакансии (1-6)
- `hh_search` — поиск вакансий
- `hh_get_vacancy` — детали вакансии
- `hh_get_employer` — информация о работодателе
- `hh_get_similar` — похожие вакансии
- `hh_get_areas` — регионы
- `hh_get_dictionaries` — справочники

### Резюме (7-9)
- `hh_get_my_resumes` — мои резюме
- `hh_get_resume` — детали резюме
- `hh_update_resume` — обновление резюме

### Отклики (10-11)
- `hh_apply_vacancy` — отклик на вакансию
- `hh_get_applications` — история откликов

### AI (12-19)
- `hh_score_vacancy` — AI скоринг вакансии (0-100)
- `hh_generate_letter` — генерация сопроводительного письма
- `hh_market_analytics` — аналитика рынка
- `hh_start_monitor` — мониторинг откликов
- `hh_career_advisor` — карьерный советник
- `hh_skills_gap` — анализ навыков
- `hh_resume_optimizer` — оптимизация резюме
- `hh_salary_forecast` — прогноз зарплаты

## ⚙️ Конфигурация MCP (settings.json)
```json
{
  "mcpServers": {
    "hh": {
      "command": "python",
      "args": ["c:\\portfolio_2026\\hh_mcp_server_v2\\src\\main.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 🚀 Запуск
### MCP сервер (через Qwen Code)
- Автоматически при старте новой сессии
- Вручную: `python src\main.py`

### Веб-дашборд
```bash
cd c:\portfolio_2026\hh_mcp_server_v2
python src\web_app.py
# http://127.0.0.1:8000
```

## 📝 Лог-файлы
- `logs/mcp_server.log` — логи MCP сервера
- `logs/web_app.log` — логи веб-дашборда

## ❗ Важные моменты
1. **API hh.ru не работает напрямую** для поиска с фильтром по зарплате — только через Playwright парсинг
2. **Авторизация** обязательна для большинства операций (телефон + SMS)
3. **MCP инструменты не работают в текущей сессии** — нужен новый чат для подключения
4. VS Code MCP поддержка встроена (Ctrl+Shift+P → MCP: Add Server)
