from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import documents, onlyoffice
from app.config import settings
from app.services.minio_service import MinioService
from app.services.onlyoffice_service import OnlyOfficeService
from app.services.redis_service import RedisService


# ---------------------------------------------------------
# Application startup / shutdown
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("======================================")
    print("Initializing application services...")
    print("======================================")

    # -----------------------------------------------------
    # Initialize MinIO
    # -----------------------------------------------------
    minio = MinioService(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
    )

    minio.ensure_bucket()

    print("MinIO initialized")


    # -----------------------------------------------------
    # Initialize Redis
    # -----------------------------------------------------
    redis = RedisService(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )

    redis.client.ping()

    print("Redis initialized")


    # -----------------------------------------------------
    # Initialize ONLYOFFICE service
    # -----------------------------------------------------
    onlyoffice_service = OnlyOfficeService(
        api_url=settings.internal_api_url,
        onlyoffice_url=settings.onlyoffice_url,
    )

    print("ONLYOFFICE service initialized")
    print(
        "ONLYOFFICE internal API URL:",
        settings.internal_api_url,
    )


    # -----------------------------------------------------
    # Inject services into Documents API
    # -----------------------------------------------------
    documents.minio_service = minio
    documents.redis_service = redis
    documents.onlyoffice_service = onlyoffice_service


    # -----------------------------------------------------
    # Inject services into ONLYOFFICE Callback API
    # -----------------------------------------------------
    onlyoffice.minio_service = minio
    onlyoffice.redis_service = redis
    onlyoffice.onlyoffice_service = onlyoffice_service


    # -----------------------------------------------------
    # Verify service injection
    # -----------------------------------------------------
    print("======================================")
    print("Services initialized successfully")
    print("======================================")
    print("MinIO:", minio)
    print("Redis:", redis)
    print("ONLYOFFICE:", onlyoffice_service)
    print("Callback Redis:", onlyoffice.redis_service)
    print("Callback MinIO:", onlyoffice.minio_service)
    print("======================================")


    yield


    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------
    print("Application shutting down...")


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="ONLYOFFICE Document Service",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API routers
# ---------------------------------------------------------
app.include_router(documents.router)
app.include_router(onlyoffice.router)


# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------

# /app/frontend/index.html inside Docker
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


@app.get("/", include_in_schema=False)
async def index():
    """Serve the document editor UI."""
    return FileResponse(INDEX_FILE)


@app.get("/index.html", include_in_schema=False)
async def index_html():
    """Serve index.html explicitly."""
    return FileResponse(INDEX_FILE)


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
