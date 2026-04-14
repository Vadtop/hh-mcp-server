# AI Career Roadmap — Vadim Titov

> Обновлено: 2026-04-14
> Целевая роль: Middle AI Developer / AI Integration Engineer
> Целевая зарплата: 150-250k удалённо
> Текущее совпадение с рынком: ~40%
> Цель: ~85% за 10 дней

---

## Сводка по рынку (10 вакансий + Dream Job)

| Навык | Вакансий | У тебя | Приоритет |
|-------|----------|--------|-----------|
| Python | 10/10 | ✅ | — |
| LLM / Prompt engineering | 8/10 | ✅ | — |
| RAG | 7/10 | ✅ | — |
| FastAPI | 6/10 | ✅ | — |
| LangChain | 5/10 | ✅ | — |
| Docker | 5/10 | ❌ | КРИТ |
| SQL / PostgreSQL | 5/10 | ❌ | КРИТ |
| Git / GitHub | 5/10 | ⚠️ слабо | КРИТ |
| Hugging Face | 4/10 | ❌ | КРИТ |
| Qdrant / FAISS | 3/10 | ❌ | ВЫСОК |
| Fine-tuning (LoRA/Unsloth) | 3/10 | ❌ | ВЫСОК |
| Английский B1-B2 | 4/10 | ❌ | ВЫСОК |
| ChromaDB | 3/10 | ✅ | — |
| OpenAI / Claude / DeepSeek | 3/10 | ✅ | — |
| GraphRAG + Neo4j | 2/10 | ❌ | СРЕД |
| Structured Output | 2/10 | ❌ | СРЕД |
| Guardrails | 2/10 | ❌ | СРЕД |
| asyncio / aiohttp | 2/10 | ❌ | СРЕД |
| pytest / тесты | 2/10 | ❌ | СРЕД |
| pandas / numpy | 2/10 | ❌ | СРЕД |
| Оптимизация LLM (батч/кэш) | 2/10 | ❌ | СРЕД |
| Реранкеры | 1/10 | ❌ | НИЗК |
| Dify | 1/10 | ❌ | НИЗК |
| Cursor / Copilot / Claude Code | 1/10 | ⚠️ юзаешь | НИЗК |
| Redis | 1/10 | ❌ | НИЗК |
| vLLM / GPU деплой | 1/10 | ❌ | НИЗК |
| MongoDB | 1/10 | ❌ | НИЗК |
| CI/CD (GitHub Actions) | 1/10 | ❌ | НИЗК |
| ONNX Runtime | 1/10 | ❌ | НИЗК |
| Whisper / TTS / STT | 1/10 | ❌ | НИЗК |
| OpenCV / YOLO / CLIP / VLM | 1/10 | ❌ | НИЗК |
| Agile / code review / git workflow | 1/10 | ⚠️ | НИЗК |
| Коммерческий опыт 2-3 года | 1/10 | ✅ 2 года | — |

---

## Навык → Проект (маппинг: каждый навык покрыт)

| Навык | Где закрывается | День |
|-------|----------------|------|
| Docker | P1 (все 4 репо) | 1 |
| SQL / PostgreSQL | P2 (sql-rag-pipeline) | 1 |
| Qdrant / FAISS | P2 (sql-rag-pipeline) | 1 |
| asyncio | P2, P12 (rag async) | 1,6 |
| Hugging Face | P3 (finetune), P4 (rag HF) | 2 |
| Fine-tuning / LoRA / Unsloth | P3 (finetune) | 2 |
| PyTorch | P3 (finetune) | 2 |
| Structured Output | P4 (rag-from-scratch) | 2 |
| Embeddings (sentence-transformers) | P4 (rag-from-scratch) | 2 |
| GraphRAG / Neo4j | P5 (graphrag-demo) | 3 |
| Реранкеры | P6 (rag-from-scratch advanced) | 3 |
| Guardrails | P6 (rag-from-scratch advanced) | 3 |
| Оптимизация LLM (батч/кэш) | P6 + P12 | 3,6 |
| Метрики RAG (recall@k, faithfulness) | P6 | 3 |
| pytest / тесты | P7, P8 | 4 |
| CI/CD (GitHub Actions) | P8 | 4 |
| Английский README | P9 | 5 |
| Dify | P11 (dify-workflow) | 6 |
| pandas / numpy / EDA | P13 (text-analytics) | 7 |
| matplotlib / seaborn | P13 | 7 |
| Рефакторинг / модульность | P14 (rag refactor) | 8 |
| Whisper / TTS / STT | P18 (whisper demo) | 10 |
| Redis | в P2 (опционально кэш) | 1 |
| vLLM / GPU | в P3 (docker GPU) | 2 |
| ONNX Runtime | бонус после P3 | — |
| OpenCV / YOLO / VLM | вне скоупа (CV-трек) | — |
| MongoDB | вне скоупа (бонус) | — |

---

## ЧТО ДЕЛАТЬ — конкретные мини-проекты

> Со мной каждый проект = 1-3 часа. Самому = 3-8 часов.
> 2 проекта в день = 10 дней на всё.

### День 1: Docker + SQL (закрывает 2 КРИТ-навыка)

- [ ] **P1: Добавить Docker во все 4 репо** (1.5ч)
  - Dockerfile + docker-compose + .dockerignore в каждый
  - Для rag-from-scratch: docker-compose с PostgreSQL
  - Для hh-mcp-server: docker-compose с Chromium
  - Коммиты: по 2-3 на репо

- [ ] **P2: sql-rag-pipeline (НОВЫЙ репо)** (2ч)
  - FastAPI + PostgreSQL + Qdrant + RAG
  - SQL: CREATE TABLE, INSERT, JOIN, GROUP BY, индексы
  - Qdrant: эмбеддинги + поиск
  - RAG endpoint: вопрос → SQL + векторный поиск → LLM → ответ
  - Docker + docker-compose (PostgreSQL + Qdrant + app)
  - Английский README + архитектурная схема
  - Покрывает: SQL, PostgreSQL, Qdrant, Docker, asyncio

### День 2: HuggingFace + Fine-tuning (закрывает 2 КРИТ-навыка)

- [ ] **P3: llm-finetuning-demo (НОВЫЙ репо)** (2ч)
  - Unsloth + LoRA fine-tune Qwen2.5-3B на своих данных (FAQ или RAG)
  - Hugging Face: загрузка модели, токенизация, инференс
  - Сравнение: до/после fine-tuning (метрики)
  - FastAPI endpoint для инференса
  - Docker (с GPU support)
  - Покрывает: HuggingFace, fine-tuning, PyTorch, Unsloth

- [ ] **P4: Добавить HuggingFace в rag-from-scratch** (1.5ч)
  - Заменить DeepSeek API на локальную модель через HuggingFace
  - Добавить embeddings через sentence-transformers (без API)
  - Structured Output endpoint (Pydantic schema → LLM)
  - Покрывает: HuggingFace, Structured Output, embeddings

### День 3: GraphRAG + Advanced RAG

- [ ] **P5: graphrag-demo (НОВЫЙ репо)** (2.5ч)
  - Neo4j + LangChain GraphRAG
  - Извлечение сущностей и связей из текста через LLM
  - Graph query: Cypher → ответ
  - FastAPI + Docker (Neo4j + app)
  - Покрывает: GraphRAG, Neo4j, Cypher

- [ ] **P6: Обновить rag-from-scratch — advanced RAG** (1.5ч)
  - Реранкер: cross-encoder после векторного поиска
  - Guardrails: проверка ответа (NeMo Guardrails или самописный)
  - Оптимизация: батчинг запросов, кэширование embeddings
  - Метрики: recall@k, faithfulness, answer relevancy
  - Покрывает: реранкеры, Guardrails, оптимизация LLM, метрики

### День 4: Тесты + CI/CD + pytest

- [ ] **P7: pytest для rag-from-scratch** (1.5ч)
  - test_api.py: endpoints
  - test_rag.py: retrieval quality
  - test_embeddings.py: embedding pipeline
  - conftest.py: fixtures, mock LLM

- [ ] **P8: pytest для hh-mcp-server** (1.5ч)
  - test_parsers.py: парсеры
  - test_scorer.py: AI скоринг
  - test_apply.py: отклики (mock)
  - GitHub Actions CI (.github/workflows/test.yml)

### День 5: Английский README + Resume

- [ ] **P9: Переписать все README на английский** (2ч)
  - rag-from-scratch → English
  - hh-mcp-server → English
  - tender-autofill → English
  - support-assistant → English (убрать "educational")
  - Добавить архитектурные схемы (mermaid)

- [ ] **P10: Обновить резюме на hh.ru** (1ч)
  - Навыки: +HuggingFace, +SQL, +PostgreSQL, +Qdrant, +Docker, +fine-tuning, +GraphRAG, +Neo4j, +pytest, +asyncio
  - "О себе": метрики, Structured Output, оптимизация LLM
  - Зарплата: 120-180k вилка
  - Скрыть "Арбитражник"
  - Английский: указать уровень

### День 6: Dify + n8n AI workflow + asyncio

- [ ] **P11: dify-ai-workflow (НОВЫЙ репо)** (1.5ч)
  - Dify: создать workflow (RAG + function calling)
  - Python SDK: интеграция через API
  - FastAPI wrapper
  - Покрывает: Dify

- [ ] **P12: Добавить asyncio в rag-from-scratch** (1.5ч)
  - aiohttp вместо requests
  - Async batch processing запросов
  - Connection pool для PostgreSQL
  - Покрывает: asyncio, aiohttp, оптимизация

### День 7: pandas + EDA + Data Science база

- [ ] **P13: text-analytics-eda (НОВЫЙ репо)** (2ч)
  - pandas + numpy: загрузка и очистка текстового датасета
  - EDA: распределение длин, токенов, языков
  - Визуализация: matplotlib/seaborn
  - RAG analytics: анализ качества ответов
  - Покрывает: pandas, numpy, scipy, matplotlib, EDA

### День 8: Рефакторинг + коммиты

- [ ] **P14: Рефакторинг rag-from-scratch** (2ч)
  - Разбить api.py на модули (routers, services, models)
  - Добавить PostgreSQL (логи + метаданные)
  - Убрать Google Sheets (или оставить опционально)
  - 10+ осмысленных коммитов

- [ ] **P15: Коммиты в hh-mcp-server** (1ч)
  - 10+ коммитов с осмысленными сообщениями
  - Обновить README после наших фиксов

### День 9: GitHub активность + промо

- [ ] **P16: Постить проекты** (1.5ч)
  - Reddit: r/MachineLearning, r/LangChain, r/LocalLLaMA
  - Telegram: @aimakerspace, @llm_ru, @python_jobs
  - Хай: "Built an MCP server for hh.ru with 19 AI tools"
  - Хай: "Fine-tuned Qwen2.5 with LoRA in 30 min on consumer GPU"

- [ ] **P17: GitHub профиль** (0.5ч)
  - Био: "AI/LLM Engineer · RAG · Agents · Automation"
  - Pinned: 6 репо (4 старых + 2 новых)
  - .github/README.md с обзором

### День 10: Бонусные навыки

- [ ] **P18: whisper-stt-demo (НОВЫЙ мини-репо)** (1.5ч)
  - Whisper STT: транскрибация аудио
  - Батчевая обработка
  - FastAPI endpoint
  - Покрывает: Speech, Whisper, батчинг

---

## Прогресс совпадения с рынком

| После дня | Навыков закрыто | Совпадение | Зарплатный потолок |
|-----------|----------------|------------|-------------------|
| Сейчас | 0 | ~40% | 120k |
| День 1 | SQL + Docker | ~55% | 150k |
| День 2 | HF + Fine-tune | ~65% | 170k |
| День 3 | GraphRAG + Advanced | ~72% | 190k |
| День 4 | Тесты + CI | ~75% | 200k |
| День 5 | README + Resume | ~78% | 200k |
| День 6 | Dify + asyncio | ~80% | 220k |
| День 7 | pandas + EDA | ~82% | 220k |
| День 8 | Рефакторинг | ~83% | 230k |
| День 9 | Промо + звёзды | ~84% | 230k |
| День 10 | Бонусы | ~85% | 250k |

---

## Конкретно по вакансиям — что закрывает каждый проект

| Вакансия | Сейчас | После 10 дней |
|----------|--------|---------------|
| Dream Job (Middle AI) | 40% | 80% |
| AI/Prompt инженер (ЛУИС+) | 55% | 90% |
| AL/ML/Prompt engineer (Плейспартс, 180k) | 45% | 85% |
| AI-разработчик Python (Social Media) | 60% | 90% |
| AI Разработчик (RB DATA, 250k) | 50% | 80% |
| Senior Backend/AI (Битсофт, 250k) | 55% | 80% |
| AI Orchestrator (Healthfull) | 40% | 70% |
| Python/ML Engineer (Фармстандарт) | 45% | 80% |
| ML-инженер GenAI (IBS) | 50% | 75% |
| Инж. AI-автоматизации (150-200k) | 45% | 80% |

---

## Сложность проектов?

**Нет, не сложные.** Каждый — это по сути:
1. Взять туториал / шаблон
2. Адаптировать под свой стек (FastAPI + Docker)
3. Добавить README + скриншот
4. Залить на GitHub

Со мной процесс:
- Я пишу код → ты проверяешь → заливаешь
- Я пишу README → ты правишь если надо
- 1 мини-проект = 1-2 часа вместе
- 2 проекта в день = реально

Самые "сложные":
- **Fine-tuning** — нужен GPU (Google Colab бесплатный подойдёт)
- **GraphRAG** — нужно поставить Neo4j (docker pull — 1 команда)
- Остальное — просто Python + FastAPI

---

## Английский — отдельный трек

- [ ] Пройти бесплатный тест на уровень (EF SET, 15 мин)
- [ ] Указать результат в резюме (даже A2 лучше чем ничего)
- [ ] Цель: B1 за 2-3 месяца (Duolingo + общение с LLM на английском)

---

## Вакансия Dream Job — статус

- Компания: Dream Job (Москва, Алтуфьевское ш.)
- Формат: удалённо / гибрид
- Собеседование: 2026-04-13
- Статус: ожидаем ответ
- Совпадение: 40% → после 4 дней = 72%
- Если позовут на тех. интервью — нужно знать: HuggingFace, RAG, SQL, оптимизация LLM

---

## Финальная цель

- GitHub: 8 репо, каждый с Docker + тесты + English README
- Навыки: все КРИТ + ВЫСОК закрыты
- Резюме: 120-180k, полный стек AI+SQL+Docker+Fine-tuning+GraphRAG
- Активность: ежедневные коммиты, 10+ звёзд
- Оффер: Middle AI Developer, удалёнка, 150-250k
