from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.resume import DictionaryResponse
from app.services.dictionaries import (
    ACADEMIC_POTENTIAL_TAGS,
    ANALYSIS_MODES,
    BEHAVIOR_TAGS,
    CAPABILITY_TAGS,
    DEGREES,
    JOB_DIRECTION_TAGS,
    METHOD_TAGS,
    RESEARCH_DIRECTION_TAGS,
    SKILL_CATEGORIES,
)

router = APIRouter(prefix="/dictionaries", tags=["dictionaries"])


@router.get("", response_model=DictionaryResponse)
def get_dictionaries(_: str = Depends(get_current_user)) -> DictionaryResponse:
    return DictionaryResponse(
        analysis_modes=ANALYSIS_MODES,
        degrees=DEGREES,
        capability_tags=CAPABILITY_TAGS,
        behavior_tags=BEHAVIOR_TAGS,
        job_direction_tags=JOB_DIRECTION_TAGS,
        research_direction_tags=RESEARCH_DIRECTION_TAGS,
        method_tags=METHOD_TAGS,
        academic_potential_tags=ACADEMIC_POTENTIAL_TAGS,
        skill_categories=SKILL_CATEGORIES,
    )
