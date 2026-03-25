from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Resume
from app.schemas.resume import ReviewSaveRequest
from app.services.repository import ResumeRepository


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ResumeRepository(db)

    def save(self, resume_id: int, payload: ReviewSaveRequest) -> Resume | None:
        resume = self.db.get(Resume, resume_id)
        if not resume:
            return None
        data = payload.model_dump()
        self.repository.replace_structured_data(resume, data)
        self.repository.create_review_version(resume, data, payload.editor)
        self.db.commit()
        self.db.refresh(resume)
        return resume

