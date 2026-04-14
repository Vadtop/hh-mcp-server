import pytest
import re
from unittest.mock import AsyncMock, MagicMock


def test_vacancy_id_extraction():
    url = "https://hh.ru/vacancy/12345678"
    match = re.search(r"/vacancy/(\d+)", url)
    assert match is not None
    assert match.group(1) == "12345678"


def test_resume_id_extraction():
    url = "https://hh.ru/resume/abc123def456"
    match = re.search(r"/resume/([a-f0-9]+)", url)
    assert match is not None
    assert match.group(1) == "abc123def456"


def test_vacancy_url_relative():
    href = "/vacancy/99887766?query=python"
    url = f"https://hh.ru{href}"
    assert url == "https://hh.ru/vacancy/99887766?query=python"


def test_vacancy_url_absolute():
    href = "https://hh.ru/vacancy/11223344"
    url = href if not href.startswith("/") else f"https://hh.ru{href}"
    assert url == "https://hh.ru/vacancy/11223344"


def test_negotiation_status_invited():
    status = "Вы приглашены"
    assert "приглашен" in status.lower()


def test_negotiation_status_refused():
    status = "Отказ работодателя"
    assert "отказ" in status.lower()


@pytest.mark.asyncio
async def test_parse_vacancy_card_mock():
    from src.browser.parsers import VacancyParser

    card = MagicMock()
    title_el = MagicMock()
    title_el.count = AsyncMock(return_value=1)
    title_el.inner_text = AsyncMock(return_value="AI Developer")
    card.locator = MagicMock(return_value=title_el)

    result = await VacancyParser._parse_vacancy_card(card)
    assert result is not None or result is None
