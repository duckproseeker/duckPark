from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ErrorBody(BaseModel):
    code: str = Field(description="错误代码")
    message: str = Field(description="错误说明")


class ApiResponse(BaseModel):
    success: bool = Field(default=True, description="请求是否成功")
    data: Any | None = Field(default=None, description="业务数据")
    error: ErrorBody | None = Field(default=None, description="错误信息")


class CreateRunRequest(BaseModel):
    descriptor: dict[str, Any] | None = Field(
        default=None,
        description="场景 descriptor 对象。与 descriptor_path 二选一。",
    )
    descriptor_path: str | None = Field(
        default=None,
        description="容器内可读的 descriptor 文件路径。与 descriptor 二选一。",
    )

    @model_validator(mode="after")
    def validate_source(self) -> CreateRunRequest:
        if self.descriptor is None and self.descriptor_path is None:
            raise ValueError("descriptor 或 descriptor_path 至少提供一个")
        return self


class RunSummary(BaseModel):
    run_id: str
    status: str
    scenario_name: str
    map_name: str
    start_time: str | None = None
    end_time: str | None = None
    error_reason: str | None = None
