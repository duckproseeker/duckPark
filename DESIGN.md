# Design Notes: Simulation Control MVP

## 1. Why API Layer and Executor Layer Are Separated

- API layer handles request validation, run creation, command issuance, and status queries.
- Executor layer exclusively handles CARLA-side lifecycle (connect/load/sync/tick/cleanup).
- This separation prevents API handlers from becoming long-running control loops and avoids direct CARLA world mutation in web threads.
- It also provides a clean boundary for future deployment scaling (independent replicas, process isolation, resource limits).

## 2. Why Only One Tick Controller in Synchronous Mode

In CARLA synchronous mode, whoever calls `world.tick()` is effectively the simulation clock owner.
If multiple components tick concurrently:
- simulation time ownership becomes ambiguous,
- actor behavior and sensor timestamps become nondeterministic,
- stop/cancel semantics can race,
- debugging and reproducibility degrade.

Therefore this MVP enforces:
- executor as the single tick authority,
- API only issues control intents,
- sync/fixed-delta setup in one place (`SimController`).

## 3. HIL Gateway Integration Path (Future) Without Breaking Current Structure

Current boundaries intentionally leave room for HIL integration:
- `app/executor/telemetry.py`: stable place to publish normalized sim telemetry.
- `app/executor/recorder.py`: extension point for synchronized recording artifacts.
- `app/executor/sim_controller.py`: single lifecycle owner where injector hooks can be added.
- `app/orchestrator/run_manager.py`: control-plane contract remains unchanged for web/API.

Planned HIL additions can be introduced as pluggable modules under executor (e.g., `injector.py`, `hil_gateway_client.py`) while preserving API contracts and run state model.

## 4. Known Limits and Next-Phase Extensions

Known limits in this MVP:
- No real sensor bridge, no DUT injection.
- No hard real-time clock sync with external hardware.
- No distributed queueing/backpressure.
- Builtin scenarios are minimal and not mapped to full ScenarioRunner/OpenSCENARIO pipelines.

Recommended next phase:
1. Add executor-side plugin interface for HIL input/output adapters.
2. Extend descriptor schema with optional `hil` section (transport, timing, channels).
3. Add OpenSCENARIO/ScenarioRunner adapter path behind current descriptor validator.
4. Add run-level heartbeat and watchdog for long-run robustness.
5. Add richer telemetry sink (Prometheus/OTLP) and bounded event retention.
