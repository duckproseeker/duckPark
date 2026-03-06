from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ErrorBody(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel):
    success: bool = True
    data: Any | None = None
    error: ErrorBody | None = None


class CreateRunRequest(BaseModel):
    descriptor: dict[str, Any] | None = None
    descriptor_path: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "CreateRunRequest":
        if self.descriptor is None and self.descriptor_path is None:
            raise ValueError("descriptor or descriptor_path is required")
        return self


class RunSummary(BaseModel):
    run_id: str
    status: str
    scenario_name: str
    map_name: str
    start_time: str | None = Field(default=None)
    end_time: str | None = Field(default=None)
    error_reason: str | None = Field(default=None)
