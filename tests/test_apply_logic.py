"""
A.3 + A.9: Тесты логики ApplyService и валидации ID.
"""

import pytest
from src.services.apply import _validate_vacancy_id
from src.services.vacancy import _validate_vacancy_id as _validate_vid_vacancy
from src.services.vacancy import _validate_employer_id
from src.services.resume import _validate_resume_id


def test_validate_vacancy_id_ok():
    assert _validate_vacancy_id("131904864") == "131904864"


def test_validate_vacancy_id_short():
    with pytest.raises(ValueError):
        _validate_vacancy_id("12345")


def test_validate_vacancy_id_injection():
    with pytest.raises(ValueError):
        _validate_vacancy_id("123/redirect")


def test_validate_vacancy_id_empty():
    with pytest.raises(ValueError):
        _validate_vacancy_id("")


def test_validate_resume_id_ok():
    assert _validate_resume_id("a1b2c3d4e5f6a7b8c9d0e1f2a3b4") == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4"


def test_validate_resume_id_short():
    with pytest.raises(ValueError):
        _validate_resume_id("abc123")


def test_validate_employer_id_ok():
    assert _validate_employer_id("12345") == "12345"


def test_validate_employer_id_injection():
    with pytest.raises(ValueError):
        _validate_employer_id("12../../admin")
