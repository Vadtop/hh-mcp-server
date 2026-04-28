FROM mcr.microsoft.com/playwright/python:v1.51.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Browsers уже встроены в base-image — не переустанавливаем

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HH_DEBUG_SCREENSHOTS=0

CMD ["python", "run_mcp.py"]
