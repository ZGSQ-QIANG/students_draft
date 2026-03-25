from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EvidenceSpan(BaseModel):
    section_id: int | None = None
    sentence_text: str
    char_span: list[int] | None = None
    field_name: str | None = None


class ApiResponse(BaseModel):
    message: str
    data: Any | None = None

