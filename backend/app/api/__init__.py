from fastapi import APIRouter
from app.api.routes import auth, projects, generation, publish, system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(generation.router)
api_router.include_router(publish.router)
api_router.include_router(system.router)
