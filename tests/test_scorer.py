import pytest
from src.ai.scorer import AIVacancyScorer, _parse_salary_string


@pytest.fixture
def scorer():
    return AIVacancyScorer()


def test_parse_salary_range():
    from_amt, to_amt = _parse_salary_string("от 100 000 до 200 000 ₽")
    assert from_amt == 100000
    assert to_amt == 200000


def test_parse_salary_single():
    from_amt, to_amt = _parse_salary_string("150 000 ₽")
    assert from_amt is None
    assert to_amt == 150000


def test_parse_salary_from():
    from_amt, to_amt = _parse_salary_string("от 80 000 ₽")
    assert from_amt == 80000
    assert to_amt is None


def test_parse_salary_empty():
    from_amt, to_amt = _parse_salary_string("")
    assert from_amt is None
    assert to_amt is None


def test_parse_salary_unicode_spaces():
    from_amt, to_amt = _parse_salary_string("от 100 000 до 200 000 ₽")
    assert from_amt == 100000
    assert to_amt == 200000


def test_skills_score_high(scorer):
    resume = ["python", "fastapi", "langchain", "docker", "rag"]
    vacancy = ["python", "fastapi", "langchain", "docker"]
    score = scorer._calculate_skills_score(resume, vacancy)
    assert score >= 70


def test_skills_score_low(scorer):
    resume = ["python", "fastapi"]
    vacancy = ["java", "spring", "kubernetes", "terraform"]
    score = scorer._calculate_skills_score(resume, vacancy)
    assert score < 30


def test_skills_score_empty(scorer):
    score = scorer._calculate_skills_score([], ["python"])
    assert score == 50.0
    score2 = scorer._calculate_skills_score(["python"], [])
    assert score2 == 50.0


def test_salary_score_match(scorer):
    score = scorer._calculate_salary_score(150000, 100000, 200000)
    assert score == 100.0


def test_salary_score_below_range(scorer):
    score = scorer._calculate_salary_score(80000, 100000, 200000)
    assert score == 80.0


def test_salary_score_above_range(scorer):
    score = scorer._calculate_salary_score(250000, 100000, 200000)
    assert score < 80


def test_salary_score_no_expected(scorer):
    score = scorer._calculate_salary_score(None, 100000, 200000)
    assert score == 50.0


def test_tfidf_similarity(scorer):
    text1 = "Python FastAPI LangChain RAG LLM Docker"
    text2 = "Python FastAPI LangChain RAG LLM Docker ChromaDB"
    score = scorer._calculate_tfidf_similarity(text1, text2)
    assert score > 50


def test_tfidf_empty(scorer):
    score = scorer._calculate_tfidf_similarity("", "some text")
    assert score == 50.0


def test_normalize_skill(scorer):
    assert scorer._normalize_skill("Py-Torch") == "py torch"
    assert scorer._normalize_skill("Machine_Learning") == "machine learning"
    assert scorer._normalize_skill("  RAG  ") == "rag"


def test_interpret_score(scorer):
    assert "Отличное" in scorer._interpret_score(95)
    assert "Хорошее" in scorer._interpret_score(78)
    assert "Среднее" in scorer._interpret_score(65)
    assert "Низкое" in scorer._interpret_score(45)
    assert "Слабое" in scorer._interpret_score(20)


def test_score_vacancy(scorer):
    vacancy = {
        "skills": ["python", "fastapi", "langchain", "docker", "rag", "llm"],
        "description": "AI Integration Engineer. RAG, LLM, Python, FastAPI, Docker.",
        "salary": "от 150 000 до 250 000 ₽",
        "remote": True,
    }
    result = scorer.score_vacancy(vacancy, expected_salary=180000)
    assert 0 <= result.score <= 100
    assert result.score_details is not None
    assert "skills_match" in result.score_details


def test_score_vacancy_no_skills(scorer):
    vacancy = {
        "skills": [],
        "description": "AI developer with Python skills",
        "salary": "",
        "remote": False,
    }
    result = scorer.score_vacancy(vacancy, expected_salary=150000)
    assert 0 <= result.score <= 100
