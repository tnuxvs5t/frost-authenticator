from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .totp import SUPPORTED_ALGORITHMS, normalize_secret


def _now() -> int:
    return int(time.time())


@dataclass
class Account:
    issuer: str
    account: str
    secret: str
    digits: int = 6
    period: int = 30
    algorithm: str = "SHA1"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: int = field(default_factory=_now)
    updated_at: int = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.issuer = self.issuer.strip()
        self.account = self.account.strip()
        self.secret = normalize_secret(self.secret)
        self.algorithm = self.algorithm.upper()
        if self.algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
        if self.digits not in (6, 7, 8):
            raise ValueError("Digits must be 6, 7, or 8")
        if not (10 <= int(self.period) <= 300):
            raise ValueError("Period must be between 10 and 300 seconds")
        self.period = int(self.period)
        if not self.issuer and not self.account:
            raise ValueError("Issuer or account is required")

    @property
    def title(self) -> str:
        if self.issuer and self.account:
            return f"{self.issuer} · {self.account}"
        return self.issuer or self.account

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "issuer": self.issuer,
            "account": self.account,
            "secret": self.secret,
            "digits": self.digits,
            "period": self.period,
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Account":
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            issuer=str(data.get("issuer") or ""),
            account=str(data.get("account") or ""),
            secret=str(data.get("secret") or ""),
            digits=int(data.get("digits") or 6),
            period=int(data.get("period") or 30),
            algorithm=str(data.get("algorithm") or "SHA1"),
            created_at=int(data.get("created_at") or _now()),
            updated_at=int(data.get("updated_at") or _now()),
        )

    def clone_with(self, **changes: Any) -> "Account":
        data = self.to_dict()
        data.update(changes)
        data["updated_at"] = _now()
        return Account.from_dict(data)
