from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Resume
from app.services.pipeline import ResumePipeline
from app.services.repository import ResumeRepository


class IngestionService:
    allowed_extensions = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".bmp"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ResumeRepository(db)
        self.pipeline = ResumePipeline(db)
        self.settings = get_settings()

    def save_uploads(self, files: list[UploadFile]) -> tuple[str, list[Resume]]:
        batch_id = uuid.uuid4().hex[:12]
        resumes: list[Resume] = []
        for file in files:
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in self.allowed_extensions:
                continue
            target_dir = self.settings.storage_path / batch_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / (file.filename or f"resume{suffix}")
            with target_path.open("wb") as output:
                shutil.copyfileobj(file.file, output)
            resume = self.repository.create_resume(
                batch_id=batch_id,
                file_name=file.filename or target_path.name,
                file_path=str(target_path),
                file_type=suffix.replace(".", ""),
            )
            resumes.append(resume)
        self.db.commit()
        for resume in resumes:
            self.db.refresh(resume)
        return batch_id, resumes

    def process_resume(self, resume_id: int) -> None:
        self.pipeline.run(resume_id)

