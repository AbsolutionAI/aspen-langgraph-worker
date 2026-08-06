from __future__ import annotations
import time, uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

Handler = Callable[[dict], None]

@dataclass
class LabBus:
    history: list[dict] = field(default_factory=list)
    _subs: dict[str, list[Handler]] = field(default_factory=lambda: defaultdict(list))

    def publish(self, subject: str, data: dict, source: str = "aspen-lgw") -> dict:
        env = {
            "id": str(uuid.uuid4()),
            "source": source,
            "type": subject,
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "specversion": "1.0",
            "data": data,
            "subject": subject,
        }
        self.history.append(env)
        for h in list(self._subs.get(subject, [])):
            h(env)
        return env

    def subscribe(self, subject: str, handler: Handler) -> None:
        self._subs[subject].append(handler)
