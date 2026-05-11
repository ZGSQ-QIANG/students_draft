from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import SessionLocal, get_db
from app.models import ExtractLog, Resume, StudentBasicInfo, StudentEducation, StudentPortrait
from app.schemas.resume import (
    ExtractLogPayload,
    ResumeDetailResponse,
    ResumeListItem,
    ResumeUploadItem,
    ReviewSaveRequest,
    SemanticSearchRequest,
    SemanticSearchResultPayload,
)
from app.services.ingestion import IngestionService
from app.services.review import ReviewService
from app.services.student_retriever import StudentRetrieverService
from app.services.dictionaries import STUDENT_MODE

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
            selectinload(Resume.papers),
            selectinload(Resume.patents),
            selectinload(Resume.competitions),
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
    batch_id, resumes = service.save_uploads(files, STUDENT_MODE)
    if not resumes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可处理的文件")
    for resume in resumes:
        background_tasks.add_task(run_resume_pipeline, resume.id)
    return {
        "batch_id": batch_id,
        "items": [
            ResumeUploadItem(
                resume_id=item.id,
                file_name=item.source_file_name,
                status=item.parse_status,
                analysis_mode=item.analysis_mode,
            ).model_dump()
            for item in resumes
        ],
    }


@router.get("", response_model=list[ResumeListItem])
def list_resumes(
    name: str | None = Query(default=None),
    school_name: str | None = Query(default=None),
    major: str | None = Query(default=None),
    student_type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResumeListItem]:
    query: Select[tuple[Resume, StudentBasicInfo, StudentEducation, StudentPortrait]] = (
        select(Resume, StudentBasicInfo, StudentEducation, StudentPortrait)
        .outerjoin(StudentBasicInfo, StudentBasicInfo.resume_id == Resume.id)
        .outerjoin(StudentEducation, StudentEducation.resume_id == Resume.id)
        .outerjoin(StudentPortrait, StudentPortrait.resume_id == Resume.id)
        .where(Resume.is_primary.is_(True))
    )

    if name:
        query = query.where(StudentBasicInfo.name.ilike(f"%{name}%"))
    if school_name:
        query = query.where(StudentEducation.school_name.ilike(f"%{school_name}%"))
    if major:
        query = query.where(StudentEducation.major.ilike(f"%{major}%"))
    if student_type:
        query = query.where(StudentPortrait.student_type == student_type)
    if keyword:
        keyword_like = f"%{keyword}%"
        query = query.where(
            or_(
                StudentBasicInfo.name.ilike(keyword_like),
                StudentEducation.school_name.ilike(keyword_like),
                StudentEducation.major.ilike(keyword_like),
                StudentPortrait.student_type.ilike(keyword_like),
                StudentPortrait.portrait_summary.ilike(keyword_like),
            )
        )

    query = query.order_by(Resume.created_at.desc())
    rows = db.execute(query).all()
    items: dict[int, ResumeListItem] = {}
    for resume, basic_info, education, portrait in rows:
        existing = items.get(resume.id)
        if existing is None:
            items[resume.id] = ResumeListItem(
                id=resume.id,
                student_id=resume.student_id,
                batch_id=resume.batch_id,
                source_file_name=resume.source_file_name,
                file_type=resume.file_type,
                student_name=basic_info.name if basic_info else None,
                school_name=education.school_name if education else None,
                major=education.major if education else None,
                student_type=portrait.student_type if portrait else None,
                analysis_mode=resume.analysis_mode,
                analysis_status=resume.analysis_status,
                parse_status=resume.parse_status,
                extract_status=resume.extract_status,
                last_error_stage=resume.last_error_stage,
                last_error_message=resume.last_error_message,
                current_version=resume.current_version,
            )
            continue
        if existing.school_name is None and education and education.school_name:
            existing.school_name = education.school_name
        if existing.major is None and education and education.major:
            existing.major = education.major
    return list(items.values())


@router.post("/semantic-search", response_model=list[SemanticSearchResultPayload])
def semantic_search_resumes(
    payload: SemanticSearchRequest,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SemanticSearchResultPayload]:
    try:
        results = StudentRetrieverService(db).search(
            payload.query,
            STUDENT_MODE,
            top_k=payload.top_k,
            chunk_types=payload.chunk_types,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return [SemanticSearchResultPayload(**item) for item in results]


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
        analysis_mode=resume.analysis_mode,
        analysis_status=resume.analysis_status,
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
        papers=resume.papers,
        patents=resume.patents,
        competitions=resume.competitions,
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
        analysis_mode=resume.analysis_mode,
        analysis_status=resume.analysis_status,
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
        papers=resume.papers,
        patents=resume.patents,
        competitions=resume.competitions,
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
