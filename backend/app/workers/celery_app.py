from __future__ import annotations

try:
    from celery import Celery
except Exception:  # pragma: no cover
    Celery = None  # type: ignore

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("student_resume_portrait", broker=settings.redis_url, backend=settings.redis_url) if Celery else None

