"""
FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    if os.getenv("DATABASE_SYNC", "false").lower() == "true":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="APSO API",
    description="FastAPI service with auto-generated CRUD endpoints",
    version="1.0.0",
    docs_url="/_docs",
    redoc_url="/_redoc",
    lifespan=lifespan,
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "APSO API", "version": "1.0.0"}


# Import and include autogen routers
# Entity routers will be registered here by the APSO CLI
# Example:
# from app.autogen.routers import organization, user
# app.include_router(organization.router, prefix="/api/organizations", tags=["Organizations"])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
