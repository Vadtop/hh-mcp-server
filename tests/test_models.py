import pytest
from src.models.vacancy import (
    Salary,
    Area,
    Employer,
    VacancyBase,
    VacancyDetail,
    VacancyScored,
    VacancyFilter,
    VacancySearchResult,
)


def test_salary_formatted_range():
    s = Salary(from_amount=100000, to_amount=200000, currency="RUR")
    assert "100,000" in s.formatted
    assert "200,000" in s.formatted
    assert "₽" in s.formatted


def test_salary_formatted_from():
    s = Salary(from_amount=150000, currency="RUR")
    assert "от" in s.formatted
    assert "₽" in s.formatted


def test_salary_formatted_to():
    s = Salary(to_amount=180000, currency="RUR")
    assert "до" in s.formatted


def test_salary_formatted_empty():
    s = Salary()
    assert "не указана" in s.formatted


def test_salary_usd():
    s = Salary(from_amount=5000, to_amount=8000, currency="USD")
    assert "$" in s.formatted


def test_vacancy_base_is_remote():
    from src.models.vacancy import Employment as Emp

    v = VacancyBase(
        id="123",
        name="Test",
        schedule=Emp(name="Удаленная работа"),
    )
    assert v.is_remote is True


def test_vacancy_base_not_remote():
    v = VacancyBase(id="123", name="Test")
    assert v.is_remote is False


def test_vacancy_base_short_description():
    v = VacancyBase(
        id="123",
        name="Test",
        snippet={"requirement": "Python and RAG"},
    )
    assert v.short_description == "Python and RAG"


def test_vacancy_detail_skills_list():
    from src.models.vacancy import KeySkill

    v = VacancyDetail(
        id="123",
        name="Test",
        key_skills=[KeySkill(name="Python"), KeySkill(name="Docker")],
    )
    assert v.skills_list == ["Python", "Docker"]


def test_vacancy_detail_description_plain():
    v = VacancyDetail(
        id="123",
        name="Test",
        description="<p>Hello <b>world</b></p>",
    )
    assert v.description_plain == "Hello world"


def test_vacancy_filter_to_params():
    f = VacancyFilter(text="AI developer", area="1", salary=150000)
    params = f.to_params()
    assert params["text"] == "AI developer"
    assert params["area"] == "1"
    assert params["salary"] == 150000


def test_vacancy_filter_empty():
    f = VacancyFilter()
    params = f.to_params()
    assert "text" not in params
    assert params["only_with_salary"] == "true"


def test_vacancy_search_result():
    r = VacancySearchResult(found=100, pages=5, per_page=20)
    assert r.found == 100
    assert r.items == []


def test_employer_logo_url():
    e = Employer(logos=[{"90": "http://logo.png", "original": "http://big.png"}])
    assert e.logo_url == "http://big.png"


def test_employer_no_logo():
    e = Employer(name="TestCorp")
    assert e.logo_url is None


def test_vacancy_scored():
    v = VacancyScored(id="123", name="Test", score=85)
    assert v.score == 85
    assert 0 <= v.score <= 100
