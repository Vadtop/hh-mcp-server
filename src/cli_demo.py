"""
CLI демо — быстрый поиск вакансий.

Запускает браузер, ищет вакансии, показывает результат.
Без MCP — напрямую через Playwright.

Использование:
    python -m src.cli_demo
    python -m src.cli_demo --query "Python разработчик" --salary 200000
"""

import asyncio
import argparse
import sys

from src.browser.engine import BrowserEngine
from src.browser.auth import HHAuth
from src.browser.parsers import VacancyParser
from src.browser.actions import BrowserActions


async def main():
    parser = argparse.ArgumentParser(description="HH.ru вакансия поиск")
    parser.add_argument("--query", default="Python разработчик", help="Поисковый запрос")
    parser.add_argument("--salary", type=int, default=None, help="Минимальная зарплата")
    parser.add_argument("--area", default=None, help="ID региона (1=Москва)")
    args = parser.parse_args()
    
    print("🚀 HH.ru — Поиск вакансий")
    print("=" * 50)
    
    browser = BrowserEngine(headless=False, slow_mo=50)
    
    try:
        await browser.start()
        auth = HHAuth(browser)
        
        # Авторизация
        print("\n🔐 Проверка авторизации...")
        if not await auth.check_auth():
            print("⚠️ Требуется авторизация")
            phone = input("📱 Номер телефона (+79XXXXXXXXX): ").strip()
            if not await auth.authenticate(phone):
                print("❌ Авторизация не удалась")
                return
            print("✅ Авторизация успешна!")
        else:
            print("✅ Сессия активна")
        
        # Поиск
        print(f"\n🔍 Поиск: {args.query}")
        if args.salary:
            print(f"💰 Зарплата: от {args.salary:,} ₽")
        if args.area:
            print(f"📍 Регион: {args.area}")
        
        page = await browser.new_page()
        actions = BrowserActions(page)
        
        # Формируем URL
        url = f"https://hh.ru/search/vacancy?text={args.query}"
        if args.salary:
            url += f"&salary={args.salary}"
        if args.area:
            url += f"&area={args.area}"
        
        await actions.goto(url)
        
        # Парсим
        vacancies = await VacancyParser.parse_search_results(page)
        
        if not vacancies:
            print("\n❌ Ничего не найдено")
            return
        
        print(f"\n📊 Найдено: {len(vacancies)} вакансий")
        print("=" * 50)
        
        for i, v in enumerate(vacancies[:10], 1):
            print(f"\n{i}. {v.get('title', '')}")
            if v.get('company'):
                print(f"   🏢 {v['company']}")
            if v.get('salary'):
                print(f"   💰 {v['salary']}")
            if v.get('location'):
                print(f"   📍 {v['location']}")
            if v.get('url'):
                print(f"   🔗 {v['url']}")
        
        print(f"\n{'='*50}")
        print("✅ Готово! Браузер открыт — можешь кликнуть и откликнуться вручную")
        
        # Ждём чтобы пользователь посмотрел
        input("\nНажми Enter для выхода...")
        
    except KeyboardInterrupt:
        print("\n👋 Завершено")
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
