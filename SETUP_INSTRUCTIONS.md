# 🚀 SETUP INSTRUCTIONS — HH MCP Server v2

## 📍 Ключевые пути

| Что | Путь |
|---|---|
| Проект | `c:\portfolio_2026\hh_mcp_server_v2\` |
| Точка входа | `c:\portfolio_2026\hh_mcp_server_v2\run_mcp.py` |
| MCP сервер | `c:\portfolio_2026\hh_mcp_server_v2\src\main.py` |
| Конфиг | `c:\portfolio_2026\hh_mcp_server_v2\src\config.py` |
| Переменные окружения | `c:\portfolio_2026\hh_mcp_server_v2\.env` |
| Сессия браузера | `c:\portfolio_2026\hh_mcp_server_v2\.browser_session\` |
| Логи | `c:\portfolio_2026\hh_mcp_server_v2\logs\` |
| **Cline MCP настройки** | `C:\Users\vtipt\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` |
| VS Code mcp.json | `c:\portfolio_2026\.vscode\mcp.json` |

---

## ✅ Статус (обновлено 13 апреля 2026)

- [x] Код написан — `src/main.py`, 19 MCP инструментов на FastMCP 3.2.3
- [x] `run_mcp.py` — корректная точка входа (добавляет проект в sys.path)
- [x] `cline_mcp_settings.json` — прописан сервер `hh-mcp`
- [x] `.vscode/mcp.json` — прописан сервер `hh_mcp_server_v2`
- [ ] `.env` — нужно создать (см. ниже)
- [ ] Playwright браузеры — нужно установить (один раз)
- [ ] Авторизация hh.ru — через телефон + SMS при первом запуске

---

## 🛠️ Первый запуск (делается один раз)

### Шаг 1: Установи зависимости

```bash
cd c:\portfolio_2026\hh_mcp_server_v2
pip install -r requirements.txt
playwright install chromium
```

Без `playwright install chromium` всё будет падать с `BrowserType.launch: Executable doesn't exist`.

### Шаг 2: Авторизуйся на hh.ru (ОБЯЗАТЕЛЬНО до запуска MCP)

**Важно:** нельзя авторизоваться через Cline — MCP сервер работает в фоне без терминала.  
Авторизация делается один раз через отдельный скрипт:

```bash
cd c:\portfolio_2026\hh_mcp_server_v2
python auth_once.py
```

Что произойдёт:
1. Откроется **видимый** браузер Chromium
2. В терминале спросит номер телефона → вводишь `+79XXXXXXXXX`
3. На телефон придёт SMS → вводишь код в терминале
4. Сессия сохранится в `.browser_session/`

После этого MCP сервер будет использовать сессию автоматически.  
Повторять авторизацию нужно только если сессия истечёт (обычно через несколько недель).

### Шаг 3: Создай `.env` (опционально — только для AI генерации писем)

```env
OPENAI_API_KEY=sk-...
```

Без него всё работает кроме `hh_generate_letter`.

### Шаг 4: Проверь что сервер стартует

```bash
python run_mcp.py
```

Должен висеть без вывода (ждёт stdin от MCP — это нормально). `Ctrl+C` для остановки.

---

## 🔌 Запуск через Cline в VS Code

### Конфигурация уже прописана в:
```
C:\Users\vtipt\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

Содержимое:
```json
{
  "mcpServers": {
    "hh-mcp": {
      "command": "python",
      "args": ["c:/portfolio_2026/hh_mcp_server_v2/run_mcp.py"],
      "env": {}
    }
  }
}
```

### Как запустить:
1. Открой VS Code
2. Открой Cline (иконка в сайдбаре или `Ctrl+Shift+P` → `Cline: Open`)
3. Нажми шестерёнку ⚙️ → **MCP Servers**
4. Сервер `hh-mcp` должен появиться — нажми **Connect** если не подключён автоматически
5. После подключения — зелёный статус и список из 19 инструментов

### Если не появляется:
- Перезапусти VS Code полностью
- Проверь `cline_mcp_settings.json` — должен быть валидный JSON
- В Cline Settings → MCP Servers → нажми "Show Output" чтобы увидеть ошибку

---

## ⚠️ Что будет работать, а что нет

**Все инструменты требуют авторизации** — `ensure_authenticated()` вызывается перед каждым запросом.  
Авторизуйся один раз через `python auth_once.py` перед первым использованием MCP.

| Инструмент | После авторизации | Нужен OpenAI? |
|---|---|---|
| `hh_search` | ✅ Работает | Нет |
| `hh_get_vacancy` | ✅ Работает | Нет |
| `hh_market_analytics` | ✅ Работает | Нет |
| `hh_score_vacancy` | ✅ Работает (TF-IDF) | Нет |
| `hh_get_my_resumes` | ✅ Работает | Нет |
| `hh_apply_vacancy` | ✅ Работает | Нет |
| `hh_generate_letter` | ✅ Работает | **Да** |
| `hh_career_advisor` | ✅ Работает | Нет |

### Если сессия истекла:
Снова запусти `python auth_once.py` — это единственный правильный способ переавторизоваться.

---

## 🔧 MCP инструменты (19 штук)

### Вакансии
- `hh_search` — поиск вакансий (text, area, salary, page)
- `hh_get_vacancy` — детали вакансии по ID
- `hh_get_employer` — информация о компании
- `hh_get_similar` — похожие вакансии
- `hh_get_areas` — список регионов
- `hh_get_dictionaries` — справочники

### Резюме
- `hh_get_my_resumes` — мои резюме
- `hh_get_resume` — детали резюме по ID
- `hh_update_resume` — обновить резюме

### Отклики
- `hh_apply_vacancy` — откликнуться на вакансию
- `hh_get_applications` — история откликов

### AI инструменты
- `hh_score_vacancy` — AI скоринг вакансии 0-100
- `hh_generate_letter` — сгенерировать сопроводительное письмо
- `hh_market_analytics` — аналитика рынка труда
- `hh_career_advisor` — карьерный советник
- `hh_skills_gap` — анализ пробелов в навыках
- `hh_resume_optimizer` — рекомендации по резюме
- `hh_salary_forecast` — прогноз зарплаты
- `hh_start_monitor` — мониторинг ответов

---

## 🆘 Частые ошибки

**`BrowserType.launch: Executable doesn't exist`**
→ Запусти `playwright install chromium`

**`ModuleNotFoundError: No module named 'fastmcp'`**
→ Запусти `pip install -r requirements.txt`

**`ModuleNotFoundError: No module named 'src'`**
→ Используй `run_mcp.py`, не `src/main.py` напрямую

**Инструменты не видны в Cline**
→ Проверь `cline_mcp_settings.json`, перезапусти VS Code

**Авторизация слетела**
→ Удали папку `.browser_session/`, авторизуйся заново через любой инструмент требующий входа
