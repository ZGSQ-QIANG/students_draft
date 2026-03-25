from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import ExtractLog


def create_log(
    db: Session,
    resume_id: int,
    stage_name: str,
    *,
    model_name: str | None = None,
    prompt_version: str | None = None,
    input_text: str | None = None,
    output: Any | None = None,
    validate_result: dict[str, Any] | None = None,
    status: str = "success",
    error_message: str | None = None,
) -> None:
    log = ExtractLog(
        resume_id=resume_id,
        stage_name=stage_name,
        model_name=model_name,
        prompt_version=prompt_version,
        input_text=input_text,
        output_text=json.dumps(output, ensure_ascii=False) if output is not None else None,
        validate_result=validate_result,
        status=status,
        error_message=error_message,
    )
    db.add(log)

