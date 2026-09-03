"""Experiment lifecycle state machine (shared contract for backend + scheduler).

Formalized lifecycle (see docs/experiment-lifecycle.md):

    CREATED -> VALIDATING -> VALIDATED -> QUEUED -> SCHEDULING -> RUNNING
       -> (CHECKPOINTING) -> COMPLETED
    SCHEDULING/RUNNING -> FAILED ; FAILED/RETRYING -> retry (relaunch) [-> SCHEDULING]

Enforced: transition() raises on any invalid transition instead of silently
allowing it. VALID_TRANSITIONS lives here and mirrors the backend contract.
"""
from typing import Final

# Statuses
CREATED: Final[str] = "CREATED"
VALIDATING: Final[str] = "VALIDATING"
VALIDATED: Final[str] = "VALIDATED"
QUEUED: Final[str] = "QUEUED"
SCHEDULING: Final[str] = "SCHEDULING"
RUNNING: Final[str] = "RUNNING"
CHECKPOINTING: Final[str] = "CHECKPOINTING"
RETRYING: Final[str] = "RETRYING"
COMPLETED: Final[str] = "COMPLETED"
FAILED: Final[str] = "FAILED"

# Experiment statuses (aggregate), used for queries and transition history.
STATUSES: Final[tuple[str, ...]] = (
    CREATED, VALIDATING, VALIDATED, QUEUED, SCHEDULING, RUNNING,
    CHECKPOINTING, RETRYING, COMPLETED, FAILED,
)

VALID_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    CREATED: frozenset({VALIDATING, FAILED}),
    VALIDATING: frozenset({VALIDATED, FAILED}),
    VALIDATED: frozenset({QUEUED, FAILED}),
    QUEUED: frozenset({SCHEDULING, FAILED}),
    SCHEDULING: frozenset({RUNNING, FAILED}),
    RUNNING: frozenset({COMPLETED, FAILED, CHECKPOINTING, RETRYING}),
    CHECKPOINTING: frozenset({RUNNING, FAILED}),
    RETRYING: frozenset({SCHEDULING, FAILED}),
    COMPLETED: frozenset(),
    FAILED: frozenset({RETRYING}),
}


def can_transition(current: str, new: str) -> bool:
    return new in VALID_TRANSITIONS.get(current, frozenset())


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""


def assert_transition(current: str, new: str) -> None:
    """Enforce: raise if the transition is invalid."""
    if not can_transition(current, new):
        raise InvalidTransitionError(
            f"Invalid transition {current} -> {new}"
        )
