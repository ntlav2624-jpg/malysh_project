from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import uuid


@dataclass
class Command:
    text: str
    command_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    mode: str = "auto"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OrganResult:
    organ: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
