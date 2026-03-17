from fastapi import APIRouter
from app.api.v1.endpoints import general

api_router = APIRouter()
api_router.include_router(general.router, tags=["general"])
