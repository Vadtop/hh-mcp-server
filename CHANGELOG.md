# Changelog

## [2.0.0] - 2026-04-28

### Fixed (Critical — A.1 to A.12)

- **A.1** Race condition in `get_browser()`: single `asyncio.Lock` caused deadlock when `get_auth()` called `get_browser()` inside same lock. Replaced with double-check pattern + lock-free fast path
- **A.2** Duplicate `HHAuth` instances across services. Replaced with singleton via DI (`get_auth()`)
- **A.3** `apply()` always returned success even on failure. Rewritten with page-state validation, button existence check, and error reporting
- **A.4** Orphan Playwright pages after exceptions. Added `safe_page` context manager — pages auto-close in `finally` block
- **A.5** Auth selectors outdated for 2026. Updated CSS selectors + added `hhtoken` cookie check as secondary validation
- **A.6** Interactive auth blocked MCP server. `allow_interactive=False` — raises instead of opening visible browser mid-session
- **A.7** Sync `openai.OpenAI` blocked event loop. Replaced with `AsyncOpenAI` throughout
- **A.8** `_parse_salary_string` crashed on empty/None input. Fixed with null-safe parsing
- **A.9** Vacancy/resume ID not validated — injection risk. Added length + character validation
- **A.10** LLM calls had no timeout — could hang forever. Added `timeout=30.0` on all OpenRouter calls
- **A.11** Dockerfile had unused `BROWSER_HEADLESS` env var and no healthcheck. Cleaned up
- **A.12** No concurrency limit on browser actions. Added `asyncio.Semaphore(5)`

### Changed

- FastMCP 0.x → 3.2.x (API migration, new server lifecycle)
- Default AI model: `google/gemini-2.5-flash` → `z-ai/glm-4.6`
- Playwright 1.40 → 1.51 with stealth settings
- `openai` sync client → `AsyncOpenAI` with 30s timeout
- User-Agent: Chrome 120 → Chrome 133 (April 2026)
- Fixed viewport → randomized from 4 common resolutions
- Resume title: hardcoded → configurable via `.env`
- Search results: `[:10]` truncation removed — returns full page
- CareerAdvisor: 2025 data → 2026 skill categories
- Cover letter format: added `for_llm` parameter for structured output
- `.gitignore`: expanded with `applied.db`, `.venv/`, `*.egg-info/`, `.DS_Store`

### Added

- `hh_health_check` — diagnostic tool showing browser, session, lock, cookie status
- `src/browser/safe_page.py` — context manager for safe Page lifecycle
- `src/services/applied_db.py` — SQLite-based application deduplication + daily limit
- `tests/test_concurrency.py` — deadlock, race condition, error recovery tests
- `tests/test_apply_logic.py` — ID validation, injection prevention
- `tests/test_applied_db.py` — deduplication and daily limit tests
- `tests/test_scorer_salary.py` — salary parsing edge cases
- `pyproject.toml` — project metadata + pytest configuration
- `.env.example` — complete template with placeholder values
- `CHANGELOG.md` — this file

### Removed

- Hardcoded `MY_SKILLS` in `scorer.py` — now reads from `.env`
- Debug screenshots from repository root
