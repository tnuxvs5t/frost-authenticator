from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from dataclasses import dataclass
from typing import Final

SUPPORTED_ALGORITHMS: Final[tuple[str, ...]] = ("SHA1", "SHA256", "SHA512")
_SECRET_RE = re.compile(r"[\s-]+")


class TOTPError(ValueError):
    """Raised when a TOTP input is invalid."""


def normalize_secret(secret: str) -> str:
    """Return a compact uppercase Base32 secret.

    Spaces and hyphens are accepted because many services display secrets in
    grouped chunks. Padding is removed and re-added only for decoding.
    """
    cleaned = _SECRET_RE.sub("", secret).strip().upper()
    if not cleaned:
        raise TOTPError("Secret cannot be empty.")
    if not re.fullmatch(r"[A-Z2-7]+=*", cleaned):
        raise TOTPError("Secret must be Base32: A-Z and 2-7, with optional '=' padding.")
    return cleaned.rstrip("=")


def decode_secret(secret: str) -> bytes:
    normalized = normalize_secret(secret)
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    try:
        return base64.b32decode(normalized + padding, casefold=True)
    except Exception as exc:  # binascii.Error varies by Python version
        raise TOTPError("Secret is not valid Base32.") from exc


def validate_algorithm(algorithm: str) -> str:
    algorithm = algorithm.upper()
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise TOTPError(f"Unsupported algorithm: {algorithm}.")
    return algorithm


def hotp(secret: str, counter: int, digits: int = 6, algorithm: str = "SHA1") -> str:
    """Generate an HOTP code as defined by RFC 4226."""
    if counter < 0:
        raise TOTPError("Counter must be non-negative.")
    if digits not in (6, 7, 8):
        raise TOTPError("Digits must be 6, 7, or 8.")
    algorithm = validate_algorithm(algorithm)
    key = decode_secret(secret)
    digestmod = getattr(hashlib, algorithm.lower())
    msg = counter.to_bytes(8, "big")
    digest = hmac.new(key, msg, digestmod).digest()
    offset = digest[-1] & 0x0F
    binary = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    code = binary % (10**digits)
    return str(code).zfill(digits)


def totp(
    secret: str,
    timestamp: int | float | None = None,
    period: int = 30,
    digits: int = 6,
    algorithm: str = "SHA1",
) -> str:
    """Generate a TOTP code as defined by RFC 6238."""
    if period <= 0:
        raise TOTPError("Period must be positive.")
    if timestamp is None:
        timestamp = time.time()
    counter = int(timestamp // period)
    return hotp(secret, counter, digits=digits, algorithm=algorithm)


def seconds_remaining(timestamp: int | float | None = None, period: int = 30) -> int:
    if period <= 0:
        raise TOTPError("Period must be positive.")
    if timestamp is None:
        timestamp = time.time()
    remaining = period - (int(timestamp) % period)
    return period if remaining == 0 else remaining


@dataclass(frozen=True)
class TOTPPreview:
    code: str
    remaining: int
    period: int


def preview(secret: str, period: int = 30, digits: int = 6, algorithm: str = "SHA1") -> TOTPPreview:
    now = time.time()
    return TOTPPreview(
        code=totp(secret, timestamp=now, period=period, digits=digits, algorithm=algorithm),
        remaining=seconds_remaining(now, period=period),
        period=period,
    )
