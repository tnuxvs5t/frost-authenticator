from __future__ import annotations

import base64
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import APP_ID
from .models import Account

VAULT_VERSION = 1
DEFAULT_ITERATIONS = 600_000


class VaultError(RuntimeError):
    """Raised when the encrypted vault cannot be read or written."""


def xdg_data_home() -> Path:
    raw = os.environ.get("XDG_DATA_HOME")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".local" / "share"


def default_vault_path() -> Path:
    return xdg_data_home() / APP_ID / "vault.json"


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text.encode("ascii"))


def _derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    if not password:
        raise VaultError("Password cannot be empty.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _fernet(password: str, salt: bytes, iterations: int) -> Fernet:
    return Fernet(_derive_key(password, salt, iterations))


def _payload(accounts: list[Account]) -> dict[str, Any]:
    return {"version": VAULT_VERSION, "accounts": [account.to_dict() for account in accounts]}


@dataclass
class VaultStore:
    path: Path = default_vault_path()

    def exists(self) -> bool:
        return self.path.exists()

    def ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except PermissionError:
            # Non-POSIX filesystems may not support chmod; continue with best effort.
            pass

    def create(self, password: str) -> list[Account]:
        if self.path.exists():
            raise VaultError(f"Vault already exists: {self.path}")
        self.save([], password=password, create_new=True)
        return []

    def load(self, password: str) -> list[Account]:
        if not self.path.exists():
            raise VaultError(f"Vault does not exist: {self.path}")
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
            crypto = envelope["crypto"]
            salt = _b64d(crypto["salt"])
            iterations = int(crypto["iterations"])
            token = envelope["token"].encode("utf-8")
        except Exception as exc:
            raise VaultError("Vault file is malformed.") from exc

        try:
            raw = _fernet(password, salt, iterations).decrypt(token)
        except InvalidToken as exc:
            raise VaultError("Wrong password or corrupted vault.") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
            if int(payload.get("version", 0)) != VAULT_VERSION:
                raise VaultError("Unsupported vault version.")
            return [Account.from_dict(item) for item in payload.get("accounts", [])]
        except VaultError:
            raise
        except Exception as exc:
            raise VaultError("Decrypted vault payload is malformed.") from exc

    def save(self, accounts: list[Account], password: str, create_new: bool = False) -> None:
        self.ensure_parent()

        if create_new or not self.path.exists():
            salt = os.urandom(16)
            iterations = DEFAULT_ITERATIONS
        else:
            try:
                envelope = json.loads(self.path.read_text(encoding="utf-8"))
                crypto = envelope["crypto"]
                salt = _b64d(crypto["salt"])
                iterations = int(crypto["iterations"])
            except Exception as exc:
                raise VaultError("Cannot read existing vault metadata for save.") from exc

        token = _fernet(password, salt, iterations).encrypt(
            json.dumps(_payload(accounts), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        envelope = {
            "version": VAULT_VERSION,
            "crypto": {
                "kdf": "pbkdf2-hmac-sha256",
                "iterations": iterations,
                "salt": _b64e(salt),
            },
            "token": token.decode("utf-8"),
        }
        self._atomic_write(envelope)

    def _atomic_write(self, envelope: dict[str, Any]) -> None:
        self.ensure_parent()
        data = json.dumps(envelope, ensure_ascii=False, indent=2) + "\n"
        fd, tmp_name = tempfile.mkstemp(prefix="vault.", suffix=".tmp", dir=str(self.path.parent), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            try:
                os.chmod(tmp_name, 0o600)
            except PermissionError:
                pass
            os.replace(tmp_name, self.path)
            try:
                self.path.chmod(0o600)
            except PermissionError:
                pass
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
