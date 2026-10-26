"""FastAPI application entrypoint for UK Wind Forecast Accuracy Analytics."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router as api_router
from backend.app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("wind_forecast_intelligence")

app = FastAPI(
    title="Wind Forecast Intelligence Backend",
    description="Analytics service for evaluating UK Day-Ahead wind generation forecast accuracy using Elexon BMRS Open Data.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend Vite/React client (including Vercel deployments)
cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
if "https://wind-forecast-omega.vercel.app" not in cors_origins:
    cors_origins.append("https://wind-forecast-omega.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/", summary="Root index")
async def root():
    """Root redirect / information endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "metadata": "/api/metadata",
        "analysis": "/api/analysis"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
