# Decision Intelligence Platform
# Multi-stage Docker image with API, test, and demo services.

FROM python:3.12-slim AS source

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY . .
RUN python -m pip install --no-cache-dir --upgrade pip

FROM source AS api
RUN python -m pip install --no-cache-dir ".[api]"
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM source AS test
RUN python -m pip install --no-cache-dir ".[dev,data,forecasting,graph,rl,api,demo]"
CMD ["pytest", "tests/", "-q", "--tb=short", "-o", "addopts="]

FROM source AS demo
RUN python -m pip install --no-cache-dir ".[demo]"
ENV DEMO_MODE=sample
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
