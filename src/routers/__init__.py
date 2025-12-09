from fastapi import APIRouter

from .tasks import router as tasks_router
from settings import settings

router = APIRouter(prefix="/api/v1", include_in_schema=settings.DEVELOP)
router.include_router(tasks_router)
