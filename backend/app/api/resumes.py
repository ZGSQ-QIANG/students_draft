from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import SessionLocal, get_db
from app.models import ExtractLog, Resume
from app.schemas.resume import (
    ExtractLogPayload,
    ResumeDetailResponse,
    ResumeListItem,
    ResumeUploadItem,
    ReviewSaveRequest,
)
from app.services.ingestion import IngestionService
from app.services.review import ReviewService

router = APIRouter(prefix="/resumes", tags=["resumes"])


def run_resume_pipeline(resume_id: int) -> None:
    db = SessionLocal()
    try:
        IngestionService(db).process_resume(resume_id)
    finally:
        db.close()


def _load_resume(db: Session, resume_id: int) -> Resume | None:
    query = (
        select(Resume)
        .where(Resume.id == resume_id)
        .options(
            selectinload(Resume.sections),
            selectinload(Resume.basic_info),
            selectinload(Resume.educations),
            selectinload(Resume.internships),
            selectinload(Resume.projects),
            selectinload(Resume.awards),
            selectinload(Resume.skills),
            selectinload(Resume.portrait),
        )
    )
    return db.execute(query).scalar_one_or_none()


@router.post("/upload", response_model=dict)
def upload_resumes(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    service = IngestionService(db)
    batch_id, resumes = service.save_uploads(files)
    if not resumes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可处理的文件")
    for resume in resumes:
        background_tasks.add_task(run_resume_pipeline, resume.id)
    return {
        "batch_id": batch_id,
        "items": [ResumeUploadItem(resume_id=item.id, file_name=item.source_file_name, status=item.parse_status).model_dump() for item in resumes],
    }


@router.get("", response_model=list[ResumeListItem])
def list_resumes(_: str = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Resume]:
    query = select(Resume).order_by(Resume.created_at.desc())
    return list(db.execute(query).scalars().all())


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume_detail(
    resume_id: int,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeDetailResponse:
    resume = _load_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在")
    return ResumeDetailResponse(
        id=resume.id,
        source_file_name=resume.source_file_name,
        parse_status=resume.parse_status,
        extract_status=resume.extract_status,
        current_version=resume.current_version,
        raw_text=resume.raw_text,
        sections=resume.sections,
        basic_info=resume.basic_info,
        educations=resume.educations,
        internships=resume.internships,
        projects=resume.projects,
        awards=resume.awards,
        skills=resume.skills,
        portrait=resume.portrait,
        last_error_stage=resume.last_error_stage,
        last_error_message=resume.last_error_message,
    )


@router.post("/{resume_id}/reprocess")
def reprocess_resume(
    resume_id: int,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在")
    background_tasks.add_task(run_resume_pipeline, resume_id)
    return {"message": "已加入重跑队列", "resume_id": resume_id}


@router.put("/{resume_id}/review", response_model=ResumeDetailResponse)
def save_review(
    resume_id: int,
    payload: ReviewSaveRequest,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeDetailResponse:
    service = ReviewService(db)
    resume = service.save(resume_id, payload)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在")
    resume = _load_resume(db, resume_id)
    assert resume is not None
    return ResumeDetailResponse(
        id=resume.id,
        source_file_name=resume.source_file_name,
        parse_status=resume.parse_status,
        extract_status=resume.extract_status,
        current_version=resume.current_version,
        raw_text=resume.raw_text,
        sections=resume.sections,
        basic_info=resume.basic_info,
        educations=resume.educations,
        internships=resume.internships,
        projects=resume.projects,
        awards=resume.awards,
        skills=resume.skills,
        portrait=resume.portrait,
        last_error_stage=resume.last_error_stage,
        last_error_message=resume.last_error_message,
    )


@router.get("/{resume_id}/logs", response_model=list[ExtractLogPayload])
def get_logs(
    resume_id: int,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExtractLog]:
    query = select(ExtractLog).where(ExtractLog.resume_id == resume_id).order_by(ExtractLog.created_at.desc())
    return list(db.execute(query).scalars().all())
