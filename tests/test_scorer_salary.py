"""
A.8: Тест _parse_salary_string для фиксированной зарплаты.
"""

from src.ai.scorer import _parse_salary_string


def test_parse_salary_fixed():
    assert _parse_salary_string("150 000 ₽") == (150000, 150000)


def test_parse_salary_from():
    assert _parse_salary_string("от 100 000 ₽") == (100000, None)


def test_parse_salary_to():
    assert _parse_salary_string("до 200 000 ₽") == (None, 200000)


def test_parse_salary_range():
    assert _parse_salary_string("от 100 000 до 200 000 ₽") == (100000, 200000)


def test_parse_salary_empty():
    assert _parse_salary_string("") == (None, None)


def test_parse_salary_none():
    assert _parse_salary_string("зарплата не указана") == (None, None)
