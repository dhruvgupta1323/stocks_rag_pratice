from fastapi import APIRouter
from backend.app.api.v1.stocks import router as stocks_router
from backend.app.api.v1.research import router as research_router
from backend.app.api.v1.evaluation import router as evaluation_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(stocks_router)
api_router.include_router(research_router)
api_router.include_router(evaluation_router)

