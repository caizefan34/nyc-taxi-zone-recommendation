# Decision Intelligence Platform
# Multi-stage Docker image with API and demo services

FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --default-timeout=300 -r requirements.txt && \
    pip install --no-cache-dir --default-timeout=300 fastapi uvicorn pydantic

# ---- API image ----
FROM base AS api

COPY . .
ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- Test image ----
FROM base AS test

COPY . .
ENV PYTHONPATH=/app

CMD ["pytest", "tests/", "-q", "--tb=short", "-o", "addopts="]

# ---- Demo image ----
FROM base AS demo

COPY . .
ENV PYTHONPATH=/app
ENV DEMO_MODE=sample
EXPOSE 8501

RUN pip install --no-cache-dir streamlit

CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
