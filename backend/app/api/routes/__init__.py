from fastapi import APIRouter
from app.api.routes import pixels, users, canvas, ai, webhooks

api_router = APIRouter()

api_router.include_router(pixels.router, prefix="/pixels", tags=["pixels"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(canvas.router, prefix="/canvas", tags=["canvas"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])