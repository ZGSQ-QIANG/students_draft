from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine


def init_db() -> None:
    settings = get_settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()
    _backfill_students()


def _apply_lightweight_migrations() -> None:
    migration_map = {
        "student": {},
        "resume": {
            "analysis_mode": "VARCHAR(32) DEFAULT 'student'",
            "analysis_status": "VARCHAR(32) DEFAULT 'uploaded'",
            "student_id": "INTEGER",
            "is_primary": "BOOLEAN DEFAULT 1",
            "dedup_fingerprint": "VARCHAR(255)",
            "duplicate_status": "VARCHAR(32) DEFAULT 'pending'",
        },
        "student_basic_info": {
            "research_interest": "TEXT",
            "target_research_direction": "TEXT",
        },
        "student_portrait": {
            "portrait_mode": "VARCHAR(32)",
            "research_direction_tags": "JSON",
            "method_tags": "JSON",
            "academic_potential_tags": "JSON",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in migration_map.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))
        connection.execute(text("UPDATE resume SET analysis_mode = 'student' WHERE analysis_mode IN ('academic', 'career') OR analysis_mode IS NULL"))
        if inspector.has_table("student"):
            connection.execute(text("UPDATE student SET analysis_mode = 'student' WHERE analysis_mode IN ('academic', 'career') OR analysis_mode IS NULL"))
        if inspector.has_table("student_resume_chunk"):
            connection.execute(
                text(
                    "UPDATE student_resume_chunk "
                    "SET analysis_mode = 'student', index_status = 'pending' "
                    "WHERE analysis_mode IN ('academic', 'career') OR analysis_mode IS NULL"
                )
            )
        if inspector.has_table("student_portrait"):
            connection.execute(
                text("UPDATE student_portrait SET portrait_mode = 'student' WHERE portrait_mode IN ('academic', 'career') OR portrait_mode IS NULL")
            )


def _backfill_students() -> None:
    from app.models import Resume
    from app.services.student_semantic_index import StudentSemanticIndexService
    from app.services.student_vector_store import StudentVectorStore
    from app.services.student_identity import StudentIdentityService

    db: Session = SessionLocal()
    try:
        resumes = db.query(Resume).order_by(Resume.created_at.asc(), Resume.id.asc()).all()
        identity_service = StudentIdentityService(db)
        vector_store = StudentVectorStore()
        reindex_resume_ids: list[int] = []
        for resume in resumes:
            resume.analysis_mode = "student"
            identity_service.resolve_resume(resume)
        for resume in resumes:
            if not resume.is_primary:
                try:
                    store = vector_store._build_store(resume.analysis_mode)
                    vector_store._delete_resume_docs(store, resume.id)
                except Exception:
                    pass
                for row in resume.resume_chunks:
                    row.index_status = "superseded"
            else:
                for row in resume.resume_chunks:
                    row.analysis_mode = "student"
                if resume.analysis_status == "completed" and (
                    not resume.resume_chunks or any(row.index_status != "indexed" for row in resume.resume_chunks)
                ):
                    reindex_resume_ids.append(resume.id)
        db.commit()
        semantic_index = StudentSemanticIndexService(db)
        for resume_id in reindex_resume_ids:
            semantic_index.reindex_resume(resume_id)
    finally:
        db.close()
