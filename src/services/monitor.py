"""
Сервис мониторинга откликов.

Реализует:
- Периодическую проверку статусов откликов
- Отслеживание изменений
- Уведомления (Console/Telegram)
- Историю откликов (JSON/SQLite)
- Генерацию отчётов
"""

import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from src.api.client import HHAPIClient
from src.api.endpoints import NEGOTIATIONS, NEGOTIATIONS_ACTIVE
from src.models.application import Application, ApplicationStatus, ApplicationStats
from src.config import (
    MONITOR_INTERVAL_SECONDS,
    NOTIFY_TELEGRAM,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    BASE_DIR,
)

logger = logging.getLogger(__name__)


class MonitorService:
    """
    Сервис мониторинга за откликами.
    
    Периодически проверяет статусы откликов и уведомляет об изменениях.
    """
    
    def __init__(
        self,
        api_client: HHAPIClient,
        interval: int = MONITOR_INTERVAL_SECONDS,
        history_file: Optional[str] = None,
    ):
        self.client = api_client
        self.interval = interval
        self.history_file = history_file or str(BASE_DIR / ".applications_history.json")
        
        # Состояние
        self._running = False
        self._previous_applications: dict[str, str] = {}  # vacancy_id -> status
        self._task: Optional[asyncio.Task] = None
        
        # Callback для уведомлений
        self._on_status_change: Optional[Callable] = None
        
        # Загружаем историю
        self._load_history()
    
    def set_callback(self, callback: Callable):
        """
        Устанавливает callback для уведомлений об изменениях.
        
        Args:
            callback: Функция(Application, old_status, new_status)
        """
        self._on_status_change = callback
    
    async def start_monitoring(self):
        """Запускает фоновый мониторинг."""
        if self._running:
            logger.warning("Мониторинг уже запущен")
            return
        
        self._running = True
        logger.info(f"Мониторинг запущен (интервал: {self.interval} сек)")
        
        # Загружаем текущие отклики
        await self._check_applications()
        
        # Запускаем цикл
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Останавливает мониторинг."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Мониторинг остановлен")
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга."""
        while self._running:
            try:
                await asyncio.sleep(self.interval)
                await self._check_applications()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _check_applications(self):
        """Проверяет текущие отклики и находит изменения."""
        logger.debug("Проверка откликов...")
        
        # Получаем активные отклики
        applications = await self.client.get(NEGOTIATIONS_ACTIVE)
        
        current_applications: dict[str, str] = {}
        
        items = applications.get("items", [])
        for item in items:
            app = Application(**item)
            vacancy_id = app.vacancy_id or ""
            status = app.status
            
            current_applications[vacancy_id] = status
            
            # Проверяем изменения
            if vacancy_id in self._previous_applications:
                old_status = self._previous_applications[vacancy_id]
                
                if old_status != status:
                    logger.info(f"Изменение статуса: {vacancy_id} {old_status} -> {status}")
                    await self._handle_status_change(app, old_status, status)
            
            self._previous_applications[vacancy_id] = status
        
        # Сохраняем историю
        self._save_history()
    
    async def _handle_status_change(
        self,
        app: Application,
        old_status: str,
        new_status: str,
    ):
        """
        Обрабатывает изменение статуса.
        
        Args:
            app: Отклик
            old_status: Старый статус
            new_status: Новый статус
        """
        status = ApplicationStatus(id=new_status, name=app.status_name)
        
        # Формируем сообщение
        message = self._format_change_message(app, old_status, new_status)
        
        # Уведомляем
        await self._send_notification(message)
        
        # Callback
        if self._on_status_change:
            self._on_status_change(app, old_status, new_status)
    
    def _format_change_message(
        self,
        app: Application,
        old_status: str,
        new_status: str,
    ) -> str:
        """Форматирует сообщение об изменении статуса."""
        old = ApplicationStatus(id=old_status, name="")
        new = ApplicationStatus(id=new_status, name=app.status_name)
        
        lines = [
            f"{new.emoji} Изменение статуса отклика!",
            "",
            f"📌 {app.vacancy_name}",
            f"🏢 {app.employer_name}",
            f"",
            f"   {old.emoji} {old_status} → {new.emoji} {new.name}",
            f"",
            f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        ]
        
        # Персонализированные сообщения
        if new_status == "invited":
            lines.append("")
            lines.append("🎉 Поздравляем! Вас пригласили на собеседование!")
        elif new_status == "refused":
            lines.append("")
            lines.append("💪 Не расстраивайтесь! Следующая вакансия будет лучше!")
        elif new_status == "offer":
            lines.append("")
            lines.append("🎊 НЕВЕРОЯТНО! Вам сделали предложение о работе!")
        
        return "\n".join(lines)
    
    async def _send_notification(self, message: str):
        """
        Отправляет уведомление.
        
        Args:
            message: Текст уведомления
        """
        # Console (всегда)
        print(f"\n{'='*50}")
        print(message)
        print(f"{'='*50}\n")
        
        # Telegram (опционально)
        if NOTIFY_TELEGRAM and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            await self._send_telegram_notification(message)
    
    async def _send_telegram_notification(self, message: str):
        """Отправляет уведомление в Telegram."""
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram уведомление отправлено")
                    else:
                        logger.error(f"Ошибка отправки Telegram: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка Telegram уведомления: {e}")
    
    def check_now(self) -> dict:
        """
        Проверяет отклики прямо сейчас (без запуска мониторинга).
        
        Returns:
            dict с результатами проверки
        """
        # Синхронная обёртка
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._check_applications_sync())
    
    async def _check_applications_sync(self) -> dict:
        """Проверяет отклики (async версия)."""
        applications = await self.client.get(NEGOTIATIONS_ACTIVE)
        items = applications.get("items", [])
        
        changes = []
        for item in items:
            app = Application(**item)
            vacancy_id = app.vacancy_id or ""
            status = app.status
            
            if vacancy_id in self._previous_applications:
                old_status = self._previous_applications[vacancy_id]
                if old_status != status:
                    changes.append({
                        "vacancy": app.vacancy_name,
                        "employer": app.employer_name,
                        "old": old_status,
                        "new": status,
                        "new_name": app.status_name,
                    })
            
            self._previous_applications[vacancy_id] = status
        
        return {
            "total": len(items),
            "changes": len(changes),
            "changes_list": changes,
        }
    
    def get_status_summary(self) -> dict:
        """
        Получает сводку текущих статусов.
        
        Returns:
            dict со сводкой
        """
        from collections import Counter
        
        counter = Counter(self._previous_applications.values())
        
        return {
            "total_active": sum(counter.values()),
            "by_status": dict(counter),
        }
    
    def _load_history(self):
        """Загружает историю из файла."""
        path = Path(self.history_file)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._previous_applications = data.get("applications", {})
                logger.debug(f"Загружена история: {len(self._previous_applications)} откликов")
            except Exception as e:
                logger.warning(f"Ошибка загрузки истории: {e}")
    
    def _save_history(self):
        """Сохраняет историю в файл."""
        try:
            path = Path(self.history_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "applications": self._previous_applications,
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Ошибка сохранения истории: {e}")
    
    def clear_history(self):
        """Очищает историю."""
        self._previous_applications.clear()
        self._save_history()
        logger.info("История очищена")
