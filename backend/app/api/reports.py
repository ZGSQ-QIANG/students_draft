from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.report import GroupReportResponse
from app.services.dictionaries import STUDENT_MODE
from app.services.group_report import GroupReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/group", response_model=GroupReportResponse)
def get_group_report(
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GroupReportResponse:
    return GroupReportService(db).build(STUDENT_MODE)
