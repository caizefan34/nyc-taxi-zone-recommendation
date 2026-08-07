"""Decision Intelligence Platform API.

FastAPI application serving zone recommendations, demand forecasting,
and fleet optimization endpoints.

Usage:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.api import router
from src.common.logging_utils import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level=logging.INFO)
    logger.info("Starting Decision Intelligence Platform API v3.0.0")
    yield
    logger.info("Shutting down API")


app = FastAPI(
    title="Urban Mobility Decision Intelligence API",
    description=(
        "Research-first, commercial-ready platform for dynamic fleet repositioning.\n\n"
        "## Important Notes\n\n"
        "- This is a research prototype. Outputs are simulation/historical-replay based.\n"
        "- Recommendations are not validated through real-world A/B testing.\n"
        "- See docs/architecture.md for architecture details."
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured request logging with latency tracking."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "%s %s %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Source"] = "simulation/historical_replay"
    return response


app.include_router(router)
