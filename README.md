# HH.ru MCP Server

AI-powered MCP server for hh.ru job search automation with 19 tools — from search to auto-apply with AI-generated cover letters.

> **Why Playwright, not API?** Since December 2025 hh.ru closed the public API for job seekers. Solution: emulate a real browser via Playwright.

---

## Features

- **Job search** — by text, salary, region, remote-only across Russia
- **Vacancy details** — full info, company profile, similar vacancies
- **Auto-apply** — one-click with AI-generated cover letter
- **AI scoring** — vacancy relevance 0–100 based on your profile
- **Market analytics** — salaries, top skills, top companies for any query
- **Career advisor** — skills gap analysis, roadmap, salary forecast
- **Response monitoring** — track application status changes (Console + Telegram)
- **Resume management** — view, update, optimize with AI recommendations

---

## Quick Start

### Docker

```bash
git clone https://github.com/Vadtop/hh-mcp-server.git
cd hh-mcp-server
cp .env.example .env  # fill in your keys
docker-compose up --build
```

### Manual

```bash
git clone https://github.com/Vadtop/hh-mcp-server.git
cd hh-mcp-server
pip install -r requirements.txt
playwright install chromium
python auth_once.py  # login to hh.ru (one time)
python run_mcp.py
```

---

## Configuration

Copy `.env.example` to `.env` and fill in:

```env
# AI (required for cover letter generation)
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=google/gemini-2.5-flash

# Your profile (for personalized letters and scoring)
MY_NAME=Your Name
MY_GITHUB=github.com/yourname
MY_TELEGRAM=@yourhandle
MY_EXPECTED_SALARY=150000
MY_WORK_FORMAT=remote
MY_RESUME_TEXT=AI Integration Engineer. RAG, LLM agents, automation...
MY_SKILLS=python,fastapi,langchain,docker,rag,llm,mcp,ai agents,...

# Notifications (optional)
NOTIFY_TELEGRAM=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### First-time Login

```bash
python auth_once.py
```

Opens a browser — enter phone and SMS code. Session persists in `.browser_session/` and is reused automatically. Re-login only when session expires (~30 days).

---

## Connecting to Cline (VS Code)

Add to `cline_mcp_settings.json` (Settings → MCP Servers):

```json
{
  "mcpServers": {
    "hh-mcp": {
      "command": "python",
      "args": ["/path/to/hh-mcp-server/run_mcp.py"],
      "cwd": "/path/to/hh-mcp-server"
    }
  }
}
```

---

## MCP Tools (19)

### Search

| Tool | Description |
|---|---|
| `hh_search` | Search by text, salary, region, remote |
| `hh_get_vacancy` | Full vacancy details by ID |
| `hh_get_employer` | Company information |
| `hh_get_similar` | Similar vacancies |

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
| `hh_update_resume` | Update title, salary, about |

### AI Analytics

| Tool | Description |
|---|---|
| `hh_score_vacancy` | AI relevance scoring 0–100 |
| `hh_market_analytics` | Salaries, top skills, top companies |
| `hh_career_advisor` | Career report: gaps, roadmap, forecast |
| `hh_skills_gap` | Skills you have vs. what's missing |
| `hh_salary_forecast` | Salary forecast after learning new skills |
| `hh_resume_optimizer` | Concrete resume improvement tips |

### Monitoring

| Tool | Description |
|---|---|
| `hh_start_monitor` | Start background response monitoring |
| `hh_stop_monitor` | Stop monitoring |
| `hh_check_monitor` | One-time status check |

---

## Example Prompts for Cline

```
Find remote AI integrator vacancies, salary from 100k
```

```
Find 20 vacancies for "AI developer" and "AI integration".
Score each via hh_score_vacancy.
Show top-10 with score above 65 with links.
```

```
Analyze the job market for "AI integrator" via hh_market_analytics
```

```
Generate a cover letter for vacancy 131782229
```

---

## Tech Stack

Python · FastMCP · Playwright · Pydantic · scikit-learn · OpenRouter API · Docker

---

## Author

[Vadim Titov](https://github.com/Vadtop)
