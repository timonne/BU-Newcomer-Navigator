"""
Shared Pydantic base classes.

`CamelModel` auto-generates camelCase aliases for every field
(full_name -> fullName, category_id -> categoryId, ...) so response
bodies match the existing frontend's TypeScript interfaces
(figma uiux/src/types/index.ts) exactly, field-for-field, with zero
mapping code needed on the frontend. FastAPI serializes response models
using their aliases by default, so returning a CamelModel from a route
is enough.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Matches the error envelope required by the project brief:
    {"error": {"code": "...", "message": "..."}}
    """

    error: ErrorDetail