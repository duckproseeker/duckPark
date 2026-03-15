"""Deprecated compatibility shim.

The active product path is ScenarioRunner-only. This import path remains only so
older references fail less abruptly while the implementation lives under
``app.deprecated.native_runtime``.
"""

from app.deprecated.native_runtime.executor.sim_controller import SimController

__all__ = ["SimController"]
