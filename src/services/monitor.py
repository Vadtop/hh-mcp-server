"""
Сервис мониторинга откликов.

Периодически проверяет статусы откликов через браузер (ApplyService),
сравнивает с предыдущим состоянием, отправляет Telegram-уведомление при изменении.
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

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
    Мониторинг откликов через браузер.

    Не требует HHAPIClient — использует ApplyService.get_applications()
    который парсит страницу hh.ru/applicant/negotiations через Playwright.
    """

    def __init__(
        self,
        apply_service,
        interval: int = MONITOR_INTERVAL_SECONDS,
        history_file: Optional[str] = None,
    ):
        self.apply_service = apply_service
        self.interval = interval
        self.history_file = Path(history_file or (BASE_DIR / ".applications_history.json"))

        self._running = False
        self._task: Optional[asyncio.Task] = None
        # vacancy_title -> status
        self._previous: dict[str, str] = {}

        self._load_history()

    async def start(self) -> str:
        """Запускает фоновый мониторинг. Возвращает статус."""
        if self._running:
            return f"⚠️ Мониторинг уже запущен (интервал: {self.interval} сек)"

        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Мониторинг запущен, интервал {self.interval} сек")

        notify = "Telegram" if (NOTIFY_TELEGRAM and TELEGRAM_BOT_TOKEN) else "Console"
        return (
            f"✅ Мониторинг запущен!\n"
            f"📊 Интервал: {self.interval} сек\n"
            f"🔔 Уведомления: {notify}"
        )

    async def stop(self) -> str:
        """Останавливает мониторинг."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Мониторинг остановлен")
        return "🛑 Мониторинг остановлен"

    async def check_now(self) -> str:
        """Разовая проверка без запуска фонового цикла."""
        changes = await self._check()
        if not changes:
            return "✅ Изменений статусов нет"
        lines = [f"🔔 Изменений: {len(changes)}"]
        for c in changes:
            lines.append(f"  • {c['title']}: {c['old']} → {c['new']}")
        return "\n".join(lines)

    # ------------------------------------------------------------------

    async def _loop(self):
        while self._running:
            try:
                await self._check()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)

    async def _check(self) -> list[dict]:
        """Сверяет текущие отклики с историей, возвращает список изменений."""
        try:
            applications = await self.apply_service.get_applications()
        except Exception as e:
            logger.error(f"Ошибка получения откликов: {e}")
            return []

        current: dict[str, str] = {}
        changes: list[dict] = []

        for app in applications:
            title = app.get("title", "")
            status = app.get("status", "")
            company = app.get("company", "")
            if not title:
                continue

            current[title] = status

            old = self._previous.get(title)
            if old is not None and old != status:
                change = {"title": title, "company": company, "old": old, "new": status}
                changes.append(change)
                logger.info(f"Смена статуса: {title!r} {old!r} → {status!r}")
                await self._notify(change)

        self._previous = current
        self._save_history()
        return changes

    async def _notify(self, change: dict):
        """Console + Telegram при изменении статуса."""
        msg = self._format_message(change)

        print(f"\n{'='*50}\n{msg}\n{'='*50}\n")

        if NOTIFY_TELEGRAM and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            await self._send_telegram(msg)

    def _format_message(self, change: dict) -> str:
        emoji_map = {
            "invited":  "🎉",
            "offer":    "🎊",
            "refused":  "😔",
            "viewed":   "👀",
        }
        new_status = change["new"].lower()
        emoji = emoji_map.get(new_status, "🔔")

        lines = [
            f"{emoji} Изменение статуса отклика!",
            f"",
            f"📌 {change['title']}",
        ]
        if change.get("company"):
            lines.append(f"🏢 {change['company']}")
        lines += [
            f"",
            f"   {change['old']} → {change['new']}",
            f"",
            f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        ]

        if new_status == "invited":
            lines.append("🎉 Вас пригласили на собеседование!")
        elif new_status == "offer":
            lines.append("🎊 Вам сделали предложение о работе!")
        elif new_status == "refused":
            lines.append("💪 Не расстраивайтесь, следующая будет лучше!")

        return "\n".join(lines)

    async def _send_telegram(self, message: str):
        try:
            import aiohttp
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info("Telegram уведомление отправлено")
                    else:
                        logger.error(f"Telegram ошибка: {resp.status}")
        except ImportError:
            logger.warning("aiohttp не установлен — Telegram уведомления недоступны")
        except Exception as e:
            logger.error(f"Ошибка Telegram: {e}")

    def _load_history(self):
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text(encoding="utf-8"))
                self._previous = data.get("applications", {})
                logger.debug(f"История загружена: {len(self._previous)} откликов")
            except Exception as e:
                logger.warning(f"Ошибка загрузки истории: {e}")

    def _save_history(self):
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "applications": self._previous,
                "updated_at": datetime.now().isoformat(),
            }
            self.history_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Ошибка сохранения истории: {e}")
