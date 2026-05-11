from fastapi import APIRouter

from app.api import auth, dictionaries, reports, resumes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dictionaries.router)
api_router.include_router(resumes.router)
api_router.include_router(reports.router)
