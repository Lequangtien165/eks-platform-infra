import json
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import JSONResponse, Response

APP_NAME = os.getenv("APP_NAME", "sample-app")
APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DOCS_URL = None if APP_ENV == "prod" else "/docs"
OPENAPI_URL = None if APP_ENV == "prod" else "/openapi.json"
START_TIME = time.time()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
APP_INFO = Gauge(
    "app_info",
    "Application info",
    ["app_name", "app_env", "app_version"],
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, self.datefmt),
        }
        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    APP_INFO.labels(
        app_name=APP_NAME,
        app_env=APP_ENV,
        app_version=APP_VERSION,
    ).set(1)
    yield


configure_logging()
logger = logging.getLogger(APP_NAME)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url=DOCS_URL,
    redoc_url=None,
    openapi_url=OPENAPI_URL,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status=str(response.status_code),
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration)

    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )
    )

    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/api/info")
async def info():
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "app_name": APP_NAME,
        "environment": APP_ENV,
        "version": APP_VERSION,
        "uptime_seconds": uptime_seconds,
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    payload = {
        "message": "sample-app is running",
        "health": "/health",
        "ready": "/ready",
        "metrics": "/metrics",
        "info": "/api/info",
    }
    if DOCS_URL:
        payload["docs"] = DOCS_URL
    return JSONResponse(payload)
