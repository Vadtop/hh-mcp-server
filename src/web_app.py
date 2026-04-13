"""
Веб-дашборд HH.ru — быстрый поиск и отклик.

Запуск:
    python -m src.web_app

Открой: http://localhost:8000
"""

import asyncio
import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.browser.parsers import VacancyParser, ResumeParser, NegotiationParser
from src.browser.actions import BrowserActions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HH.ru Dashboard")

# Глобальный браузер
_browser: BrowserEngine = None


@app.on_event("startup")
async def startup():
    global _browser
    _browser = BrowserEngine(headless=False, slow_mo=50)
    await _browser.start()
    logger.info("✅ Браузер запущен")


@app.on_event("shutdown")
async def shutdown():
    global _browser
    if _browser:
        await _browser.close()
    logger.info("👋 Браузер закрыт")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HH.ru Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #f5f5f5; }
        .header { background: #303233; color: white; padding: 20px; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; color: #333; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        button { background: #0f8; border: none; color: white; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: 600; }
        button:hover { background: #0c6; }
        .vacancy { border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
        .vacancy:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .vacancy h3 { color: #05f; margin-bottom: 5px; }
        .vacancy a { color: #05f; text-decoration: none; }
        .salary { color: #0a0; font-weight: 600; }
        .company { color: #666; }
        .location { color: #999; font-size: 14px; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .status.auth { background: #d4edda; color: #155724; }
        .status.unauth { background: #fff3cd; color: #856404; }
        .loading { text-align: center; padding: 40px; color: #666; }
        #results { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 HH.ru Dashboard</h1>
        <p>Поиск вакансий через Playwright</p>
    </div>
    <div class="container">
        <!-- Статус авторизации -->
        <div class="card">
            <h3>🔐 Статус</h3>
            <div id="auth-status" class="loading">Проверка...</div>
        </div>

        <!-- Поиск -->
        <div class="card">
            <h3>🔍 Поиск вакансий</h3>
            <form id="search-form" onsubmit="searchVacancies(event)">
                <div class="form-group">
                    <label>Поисковый запрос</label>
                    <input type="text" id="query" value="Python разработчик" placeholder="Должность, ключевые слова">
                </div>
                <div class="form-group">
                    <label>Минимальная зарплата (₽)</label>
                    <input type="number" id="salary" value="200000" placeholder="0">
                </div>
                <div class="form-group">
                    <label>Регион</label>
                    <select id="area">
                        <option value="1">Москва</option>
                        <option value="2">Санкт-Петербург</option>
                        <option value="">Вся Россия</option>
                    </select>
                </div>
                <button type="submit">🔍 Найти</button>
            </form>
        </div>

        <!-- Результаты -->
        <div class="card">
            <h3 id="results-title">Результаты</h3>
            <div id="results"></div>
        </div>
    </div>

    <script>
        // Проверка авторизации
        async function checkAuth() {
            const resp = await fetch('/api/auth/check');
            const data = await resp.json();
            const el = document.getElementById('auth-status');
            if (data.authenticated) {
                el.innerHTML = '<span class="status auth">✅ Авторизован</span>';
            } else {
                el.innerHTML = '<span class="status unauth">⚠️ Не авторизован — <a href="#" onclick="login()">войти</a></span>';
            }
        }

        // Вход
        async function login() {
            const phone = prompt('Введите номер телефона (+79XXXXXXXXX):');
            if (!phone) return;
            
            const resp = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone})
            });
            const data = await resp.json();
            if (data.needs_code) {
                const code = prompt('Введите код из SMS:');
                await fetch('/api/auth/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({code})
                });
            }
            checkAuth();
        }

        // Поиск вакансий
        async function searchVacancies(e) {
            e.preventDefault();
            const query = document.getElementById('query').value;
            const salary = document.getElementById('salary').value;
            const area = document.getElementById('area').value;
            
            document.getElementById('results').innerHTML = '<div class="loading">⏳ Ищу вакансии...</div>';
            
            const params = new URLSearchParams({query, area});
            if (salary) params.set('salary', salary);
            
            const resp = await fetch(`/api/search?${params}`);
            const data = await resp.json();
            
            const title = document.getElementById('results-title');
            const results = document.getElementById('results');
            
            if (data.error) {
                title.textContent = 'Ошибка';
                results.innerHTML = `<p style="color:red">${data.error}</p>`;
                return;
            }
            
            title.textContent = `📊 Найдено: ${data.vacancies.length} вакансий`;
            
            if (!data.vacancies.length) {
                results.innerHTML = '<p>Ничего не найдено</p>';
                return;
            }
            
            results.innerHTML = data.vacancies.map((v, i) => `
                <div class="vacancy">
                    <h3>${i+1}. <a href="${v.url}" target="_blank">${v.title || 'Без названия'}</a></h3>
                    ${v.company ? `<p class="company">🏢 ${v.company}</p>` : ''}
                    ${v.salary ? `<p class="salary">💰 ${v.salary}</p>` : ''}
                    ${v.location ? `<p class="location">📍 ${v.location}</p>` : ''}
                </div>
            `).join('');
        }

        // Инициализация
        checkAuth();
    </script>
</body>
</html>
"""


@app.get("/api/auth/check")
async def check_auth():
    global _browser
    if not _browser:
        return {"authenticated": False}
    
    auth = HHAuth(_browser)
    is_auth = await auth.check_auth()
    return {"authenticated": is_auth}


@app.post("/api/auth/login")
async def login(request: Request):
    """Начинает авторизацию — открывает браузер для ввода SMS."""
    global _browser
    data = await request.json()
    phone = data.get("phone", "")
    
    if not phone:
        return {"error": "Нужен номер телефона"}
    
    auth = HHAuth(_browser)
    # Авторизация интерактивная — браузер уже открыт
    success = await auth.authenticate(phone)
    
    return {"authenticated": success, "needs_code": True}


@app.get("/api/search")
async def search(query: str, salary: int = None, area: str = None):
    global _browser
    
    if not _browser:
        return {"error": "Браузер не запущен"}
    
    auth = HHAuth(_browser)
    if not await auth.ensure_authenticated():
        return {"error": "Не авторизован"}
    
    from src.services.vacancy import VacancyService
    service = VacancyService(_browser)
    
    result = await service.search(text=query, salary=salary, area=area)
    
    return {
        "vacancies": result.get("vacancies", []),
        "found": result.get("found", 0),
    }


@app.get("/api/resumes")
async def get_resumes():
    global _browser
    if not _browser:
        return {"error": "Браузер не запущен"}
    
    auth = HHAuth(_browser)
    if not await auth.ensure_authenticated():
        return {"error": "Не авторизован"}
    
    from src.services.resume import ResumeService
    service = ResumeService(_browser)
    resumes = await service.get_my_resumes()
    
    return {"resumes": resumes}


@app.get("/api/applications")
async def get_applications():
    global _browser
    if not _browser:
        return {"error": "Браузер не запущен"}
    
    auth = HHAuth(_browser)
    if not await auth.ensure_authenticated():
        return {"error": "Не авторизован"}
    
    from src.services.apply import ApplyService
    service = ApplyService(_browser)
    applications = await service.get_applications()
    
    return {"applications": applications}


if __name__ == "__main__":
    print("🚀 Запуск HH.ru Dashboard...")
    print("🌐 Открой: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
