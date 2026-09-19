import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.core.config import settings
from app.database.session import engine

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("orderflow")
app = FastAPI(title="OrderFlow API", version="1.0.0", description="Order and inventory management API")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix=settings.api_prefix)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Request validation failed", "details": exc.errors()}})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)}} , headers=exc.headers)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An unexpected server error occurred"}})


@app.get("/health", tags=["system"])
def health():
    try:
        with engine.connect() as connection: connection.execute(text("SELECT 1"))
        return {"status": "healthy", "application": "healthy", "database": "healthy"}
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "application": "healthy", "database": "unhealthy"})
