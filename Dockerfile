FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_LLM_EXPLAINER=false

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir --requirement requirements-docker.txt

COPY app ./app
COPY core ./core
COPY prompts ./prompts

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
