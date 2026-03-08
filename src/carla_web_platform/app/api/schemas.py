from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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
    hil_config: HilConfigPayload | None = Field(
        default=None,
        description="阶段二 HIL 运行配置。未提供时保持当前纯 CARLA 控制模式。",
    )
    evaluation_profile: EvaluationProfilePayload | None = Field(
        default=None,
        description="阶段二评测配置。未提供时不绑定评测模板。",
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


class HilConfigPayload(BaseModel):
    mode: str = Field(default="camera_open_loop")
    gateway_id: str
    video_source: str = Field(default="hdmi_x1301")
    dut_input_mode: str = Field(default="uvc_camera")
    result_ingest_mode: str = Field(default="http_push")

    @field_validator(
        "mode", "gateway_id", "video_source", "dut_input_mode", "result_ingest_mode"
    )
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()


class EvaluationProfilePayload(BaseModel):
    profile_name: str = Field(default="yolo_open_loop_v1")
    metrics: list[str] = Field(
        default_factory=lambda: [
            "precision",
            "recall",
            "map50",
            "avg_latency_ms",
            "p95_latency_ms",
            "fps",
            "frame_drop_rate",
        ]
    )
    iou_threshold: float = Field(default=0.5, ge=0.1, le=1.0)
    classes: list[str] = Field(default_factory=list)

    @field_validator("profile_name")
    @classmethod
    def validate_profile_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("profile_name must not be empty")
        return value.strip()


class WeatherPayload(BaseModel):
    preset: str = Field(default="ClearNoon")
    cloudiness: float | None = Field(default=None, ge=0.0, le=100.0)
    precipitation: float | None = Field(default=None, ge=0.0, le=100.0)
    precipitation_deposits: float | None = Field(default=None, ge=0.0, le=100.0)
    wind_intensity: float | None = Field(default=None, ge=0.0, le=100.0)
    wetness: float | None = Field(default=None, ge=0.0, le=100.0)
    fog_density: float | None = Field(default=None, ge=0.0, le=100.0)
    sun_altitude_angle: float | None = Field(default=None, ge=-90.0, le=90.0)
    sun_azimuth_angle: float | None = Field(default=None, ge=0.0, le=360.0)

    @field_validator("preset")
    @classmethod
    def validate_preset(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("weather preset must not be empty")
        return value.strip()


class RunEnvironmentUpdateRequest(BaseModel):
    weather: WeatherPayload
    debug: dict[str, Any] | None = None


class GatewayRegisterRequest(BaseModel):
    gateway_id: str
    name: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    agent_version: str | None = None
    address: str | None = None

    @field_validator("gateway_id", "name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()


class GatewayHeartbeatRequest(BaseModel):
    status: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    current_run_id: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("status must not be empty")
        return value.strip().upper()


class CreateCaptureRequest(BaseModel):
    gateway_id: str
    source: str = Field(default="hdmi_x1301")
    save_format: str = Field(default="jpg")
    sample_fps: float = Field(default=2.0, gt=0.0, le=30.0)
    max_frames: int = Field(default=300, ge=1, le=100000)
    save_dir: str
    note: str | None = None

    @field_validator("gateway_id", "source", "save_format", "save_dir")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in {"hdmi_x1301", "frame_stream"}:
            raise ValueError("source must be one of: hdmi_x1301, frame_stream")
        return normalized

    @field_validator("save_format")
    @classmethod
    def validate_save_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"jpg", "png", "raw"}:
            raise ValueError("save_format must be one of: jpg, png, raw")
        return normalized


class CaptureFramePayload(BaseModel):
    frame_index: int = Field(ge=0)
    captured_at_utc: str | None = None
    relative_path: str
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    size_bytes: int | None = Field(default=None, ge=0)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("relative_path must not be empty")
        return value.strip()


class CaptureSyncRequest(BaseModel):
    status: str | None = None
    saved_frames: int | None = Field(default=None, ge=0)
    error_reason: str | None = None
    frames: list[CaptureFramePayload] | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("status must not be empty")
        return value.strip().upper()


class BenchmarkTaskScenarioMatrixItemPayload(BaseModel):
    scenario_id: str
    map_name: str
    environment_preset_id: str
    sensor_profile_name: str

    @field_validator(
        "scenario_id", "map_name", "environment_preset_id", "sensor_profile_name"
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()


class CreateBenchmarkTaskRequest(BaseModel):
    project_id: str
    benchmark_definition_id: str
    dut_model: str | None = None
    scenario_matrix: list[BenchmarkTaskScenarioMatrixItemPayload] = Field(
        default_factory=list
    )
    hil_config: HilConfigPayload | None = None
    evaluation_profile_name: str | None = None
    auto_start: bool = False

    @field_validator("project_id", "benchmark_definition_id")
    @classmethod
    def validate_entity_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()

    @field_validator("dut_model")
    @classmethod
    def validate_dut_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ReportExportRequest(BaseModel):
    benchmark_task_id: str

    @field_validator("benchmark_task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("benchmark_task_id must not be empty")
        return value.strip()
