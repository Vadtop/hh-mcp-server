# HH.ru MCP Server v2.0.0 — AI-powered job hunting after API shutdown

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastMCP 3.2](https://img.shields.io/badge/FastMCP-3.2-green.svg)
![Tests 60/60](https://img.shields.io/badge/tests-60%2F60-brightgreen.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)

## Why

On December 15, 2025, hh.ru shut down its public API for job seekers. No more `/vacancies` endpoint, no programmatic search, no auto-apply. This server restores full automation by emulating a real browser session via Playwright — search, scoring, cover letters, applications — all through MCP tools callable from any AI assistant.

## What's new in v2

- **Stealth Playwright** — Chrome 133 UA, randomized viewport, anti-bot delays, cookie-based auth persistence
- **GLM-4.6 default model** — via OpenRouter, replaces Gemini; async OpenAI client with 30s timeout
- **FastMCP 3.2.x** — migrated from FastMCP 0.x; stdio + streamable-http transport
- **Deduplication DB** — SQLite-backed `applied.db` prevents duplicate applications
- **Daily application limit** — configurable `MAX_APPLIES_PER_DAY` (default 20)
- **Deadlock-free init** — double-check locking with `asyncio.wait_for` timeout; no more hung browser-tools
- **Error recovery** — failed `browser.start()` resets state; next call retries clean
- **`hh_health_check`** — diagnostic tool for browser, session, lock status
- **Safe page context manager** — pages auto-close after use; no orphan tab leaks
- **60 unit tests** — concurrency, scoring, parsing, apply logic, deduplication

## Quick Start

```bash
git clone https://github.com/YOURNAME/hh-mcp-server.git
cd hh-mcp-server
pip install -r requirements.txt
playwright install chromium
playwright install-deps          # Linux only
cp .env.example .env             # fill in your keys
python auth_once.py              # login to hh.ru (one time)
python run_mcp.py                # starts MCP server on stdio
```

### First-time Login

```bash
python auth_once.py
```

Opens a visible Chromium window — enter your phone and SMS code on hh.ru. Session (cookies + localStorage) persists in `.browser_session/` and is reused automatically. Re-login only when session expires (~30 days).

## MCP Tools (20)

### Search & Browsing

| Tool | Description |
|---|---|
| `hh_search` | Search vacancies by text, salary, region, remote |
| `hh_get_vacancy` | Full vacancy details by ID |
| `hh_get_employer` | Company information |
| `hh_get_similar` | Find similar vacancies |
| `hh_bulk_search` | Search multiple queries at once (remote, all Russia) |
| `hh_health_check` | Diagnostic: browser, session, lock status |

### Applications

| Tool | Description |
|---|---|
| `hh_apply_vacancy` | Apply with AI-generated cover letter |
| `hh_get_applications` | Application history and statuses |
| `hh_generate_letter` | Generate letter without sending |

### Resume

| Tool | Description |
|---|---|
| `hh_get_my_resumes` | List all resumes |
| `hh_get_resume` | Resume details by ID |
| `hh_update_resume` | Update title, salary, about section |

### AI Analytics

| Tool | Description |
|---|---|
| `hh_score_vacancy` | AI relevance scoring 0–100 (TF-IDF + skills + salary) |
| `hh_market_analytics` | Salaries, top skills, top companies for any query |
| `hh_career_advisor` | Career report: gaps, roadmap, forecast |
| `hh_skills_gap` | Skills you have vs. what the market wants |
| `hh_salary_forecast` | Salary forecast after learning new skills |
| `hh_resume_optimizer` | Concrete resume improvement tips |

### Monitoring

| Tool | Description |
|---|---|
| `hh_start_monitor` | Start background response monitoring |
| `hh_stop_monitor` | Stop monitoring |
| `hh_check_monitor` | One-time application status check |

## Connect to Clients

### opencode

Add to your project's `opencode.json`:

```json
{
  "mcpServers": {
    "hh-mcp": {
      "command": "python",
      "args": ["run_mcp.py"],
      "cwd": "/path/to/hh-mcp-server"
    }
  }
}
```

### VS Code (Cline / Continue)

Add to `.vscode/mcp.json` or your MCP settings:

```json
{
  "servers": {
    "hh-mcp": {
      "command": "python",
      "args": ["run_mcp.py"],
      "cwd": "/path/to/hh-mcp-server"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hh-mcp": {
      "command": "python",
      "args": ["run_mcp.py"],
      "cwd": "/path/to/hh-mcp-server"
    }
  }
}
```

## Architecture

```
┌─────────────────────────────────┐
│          MCP Client             │  (opencode / Claude / VS Code)
│  calls tools via stdio/HTTP     │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│       FastMCP 3.2 Server        │  20 tools, lazy init, semaphore(5)
└──────┬─────────┬───────────────┘
       │         │
┌──────▼──┐ ┌───▼──────────────┐
│ Services │ │   AI Layer       │
│ vacancy  │ │  scorer (TF-IDF) │
│ apply    │ │  letter_gen      │  OpenRouter → GLM-4.6
│ resume   │ │  career_advisor  │
│ monitor  │ │  market_analyzer │
└──────┬───┘ └──────────────────┘
       │
┌──────▼──────────────────────────┐
│       Browser Layer             │
│  Playwright + Chromium          │  Chrome 133 UA, stealth
│  safe_page ctx manager          │  random viewport, anti-bot
│  auth (cookie persistence)      │  .browser_session/storage.json
└─────────────────────────────────┘
```

## Disclaimer

This project automates interactions with hh.ru via browser emulation. Usage may violate hh.ru's Terms of Service. The author assumes no responsibility for:
- Account restrictions or bans imposed by hh.ru
- Rate limiting or CAPTCHA challenges
- Any consequences of automated job applications

Use responsibly. Set reasonable `MAX_APPLIES_PER_DAY` and `SCORING_THRESHOLD` values. Review cover letters before sending. This tool is intended for personal use only.

## License

MIT
