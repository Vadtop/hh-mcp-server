"""
A.1: Тест race condition + deadlock + error recovery в get_browser.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_browser_creates_only_once():
    start_count = 0

    original_start = AsyncMock()

    async def mock_start(self):
        nonlocal start_count
        start_count += 1
        self._initialized = True
        self._context = MagicMock()
        return self._context

    with patch("src.main.BrowserEngine") as MockEngine:
        instance = MagicMock()
        instance.start = mock_start.__get__(instance, MagicMock)
        instance._initialized = False
        instance._context = None
        MockEngine.return_value = instance

        from src import main as m

        m._browser = None
        m._browser_started = False
        m._auth = None
        m._vacancy_service = None
        m._resume_service = None
        m._apply_service = None

        async def call_get_browser():
            return await m.get_browser()

        results = await asyncio.gather(
            call_get_browser(),
            call_get_browser(),
            call_get_browser(),
            call_get_browser(),
            call_get_browser(),
        )

        assert start_count == 1, f"Browser start() вызван {start_count} раз вместо 1"
        assert all(r is instance for r in results)


@pytest.mark.asyncio
async def test_get_browser_no_deadlock_with_get_auth():
    """get_auth() вызывает get_browser() — не должно быть дедлока на _init_lock."""

    async def mock_start(self):
        self._initialized = True
        self._context = MagicMock()
        self._context.cookies = AsyncMock(return_value=[])
        return self._context

    with patch("src.main.BrowserEngine") as MockEngine:
        instance = MagicMock()
        instance.start = mock_start.__get__(instance, MagicMock)
        instance._initialized = False
        instance._context = None
        MockEngine.return_value = instance

        from src import main as m

        m._browser = None
        m._browser_started = False
        m._auth = None
        m._vacancy_service = None
        m._resume_service = None
        m._apply_service = None

        auth = await m.get_auth()
        assert auth is not None
        assert m._browser_started is True


@pytest.mark.asyncio
async def test_get_browser_resets_on_failure():
    """Если start() падает — _browser сбрасывается в None, следующий вызов пробует заново."""

    call_count = 0

    async def mock_start_fail_then_ok(self):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Chromium crashed")
        self._initialized = True
        self._context = MagicMock()
        return self._context

    with patch("src.main.BrowserEngine") as MockEngine:
        instance_fail = MagicMock()
        instance_fail.start = mock_start_fail_then_ok.__get__(instance_fail, MagicMock)
        instance_fail._initialized = False
        instance_fail._context = None
        instance_fail.close = AsyncMock()

        MockEngine.return_value = instance_fail

        from src import main as m

        m._browser = None
        m._browser_started = False
        m._auth = None

        with pytest.raises(RuntimeError, match="Chromium crashed"):
            await m.get_browser()

        assert m._browser is None, "После ошибки _browser должен быть None"
        assert m._browser_started is False, "После ошибки _browser_started должен быть False"

        result = await m.get_browser()
        assert result is not None
        assert call_count == 2
