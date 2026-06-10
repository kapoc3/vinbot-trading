from fastapi import APIRouter
from app.api.v1.endpoints import general, backtest, dashboard

api_router = APIRouter()
api_router.include_router(general.router, tags=["general"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
