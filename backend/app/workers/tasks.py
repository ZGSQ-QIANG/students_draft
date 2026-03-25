from __future__ import annotations

from app.db.session import SessionLocal
from app.services.pipeline import ResumePipeline
from app.workers.celery_app import celery_app


if celery_app:

    @celery_app.task(name="parse_resume")
    def parse_resume(resume_id: int) -> None:
        db = SessionLocal()
        try:
            ResumePipeline(db).run(resume_id)
        finally:
            db.close()

