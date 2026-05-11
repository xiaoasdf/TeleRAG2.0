from __future__ import annotations

from threading import Lock


class TaskStateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._states: dict[str, dict[str, object]] = {}

    def set(self, kb_id: str, **values: object) -> dict[str, object]:
        with self._lock:
            current = dict(self._states.get(kb_id, {}))
            current.update(values)
            self._states[kb_id] = current
            return dict(current)

    def get(self, kb_id: str) -> dict[str, object]:
        with self._lock:
            return dict(self._states.get(kb_id, {}))
