from __future__ import annotations

from typing import Any

ENVIRONMENT_PRESETS: list[dict[str, Any]] = [
    {
        "preset_id": "clear_day",
        "display_name": "Clear Day",
        "description": "标准白天晴天，适合作为基线回归场景。",
        "weather": {"preset": "ClearNoon", "sun_altitude_angle": 68.0},
    },
    {
        "preset_id": "cloudy_day",
        "display_name": "Cloudy Day",
        "description": "多云日间，适合测试曝光和识别鲁棒性。",
        "weather": {"preset": "CloudyNoon", "cloudiness": 65.0},
    },
    {
        "preset_id": "wet_road",
        "display_name": "Wet Road",
        "description": "路面潮湿但降雨轻微，适合路面反光与检测退化分析。",
        "weather": {
            "preset": "WetNoon",
            "wetness": 60.0,
            "precipitation_deposits": 45.0,
        },
    },
    {
        "preset_id": "hard_rain",
        "display_name": "Hard Rain",
        "description": "强降雨与高湿环境，用于极端开环感知压测。",
        "weather": {
            "preset": "HardRainNoon",
            "precipitation": 85.0,
            "wetness": 85.0,
            "fog_density": 20.0,
        },
    },
    {
        "preset_id": "low_sun_evening",
        "display_name": "Low Sun Evening",
        "description": "低太阳高度角，适合背光和黄昏场景。",
        "weather": {
            "preset": "ClearSunset",
            "sun_altitude_angle": 12.0,
            "sun_azimuth_angle": 220.0,
        },
    },
]


def list_environment_presets() -> list[dict[str, Any]]:
    return [dict(item) for item in ENVIRONMENT_PRESETS]
