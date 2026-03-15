from __future__ import annotations

from pathlib import Path

from app.executor.sensor_recorder import SensorRecorder


class FakeHandle:
    def __init__(self, events: list[str], name: str) -> None:
        self._events = events
        self._name = name

    def close(self) -> None:
        self._events.append(f"close:{self._name}")


class FakeSensorActor:
    def __init__(self, events: list[str], name: str) -> None:
        self._events = events
        self._name = name

    def listen(self, callback) -> None:
        assert callable(callback)
        self._events.append(f"listen:{self._name}")

    def stop(self) -> None:
        self._events.append(f"stop:{self._name}")

    def destroy(self) -> None:
        self._events.append(f"destroy:{self._name}")


def test_sensor_recorder_stop_detaches_callbacks_before_destroy(
    tmp_path: Path, monkeypatch
) -> None:
    events: list[str] = []
    recorder = SensorRecorder(
        host="127.0.0.1",
        port=2000,
        timeout_seconds=10.0,
        output_root=tmp_path,
    )
    recorder._jsonl_handles = {
        "front": FakeHandle(events, "front"),
        "rear": FakeHandle(events, "rear"),
    }
    recorder._spawned_sensors = [
        FakeSensorActor(events, "front"),
        FakeSensorActor(events, "rear"),
    ]
    recorder._hero_actor = object()
    recorder._world = object()
    recorder._client = object()
    recorder._carla = object()

    monkeypatch.setattr(
        "app.executor.sensor_recorder.time.sleep",
        lambda seconds: events.append(f"sleep:{seconds}"),
    )

    recorder.stop()

    assert events == [
        "close:front",
        "close:rear",
        "listen:rear",
        "stop:rear",
        "listen:front",
        "stop:front",
        "sleep:0.2",
        "destroy:rear",
        "destroy:front",
    ]
    assert recorder._spawned_sensors == []
    assert recorder._jsonl_handles == {}
    assert recorder._hero_actor is None
    assert recorder._world is None
    assert recorder._client is None
    assert recorder._carla is None
