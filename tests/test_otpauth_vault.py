from pathlib import Path

import pytest

from frost_authenticator.models import Account
from frost_authenticator.otpauth import build_otpauth_uri, parse_otpauth_uri
from frost_authenticator.vault import VaultError, VaultStore


def test_parse_google_style_otpauth_uri() -> None:
    account = parse_otpauth_uri(
        "otpauth://totp/Example:alice%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example&algorithm=SHA1&digits=6&period=30"
    )
    assert account.issuer == "Example"
    assert account.account == "alice@example.com"
    assert account.secret == "JBSWY3DPEHPK3PXP"
    assert account.digits == 6
    assert account.period == 30


def test_otpauth_round_trip() -> None:
    original = Account(issuer="Service", account="me@example.com", secret="JBSWY3DPEHPK3PXP")
    parsed = parse_otpauth_uri(build_otpauth_uri(original))
    assert parsed.issuer == original.issuer
    assert parsed.account == original.account
    assert parsed.secret == original.secret


def test_vault_round_trip(tmp_path: Path) -> None:
    store = VaultStore(tmp_path / "vault.json")
    account = Account(issuer="Example", account="alice", secret="JBSWY3DPEHPK3PXP")
    store.save([account], password="correct horse battery staple", create_new=True)
    loaded = store.load("correct horse battery staple")
    assert [item.to_dict() for item in loaded] == [account.to_dict()]
    raw = store.path.read_text(encoding="utf-8")
    assert "JBSWY3DPEHPK3PXP" not in raw


def test_vault_rejects_wrong_password(tmp_path: Path) -> None:
    store = VaultStore(tmp_path / "vault.json")
    store.save([], password="correct horse battery staple", create_new=True)
    with pytest.raises(VaultError):
        store.load("wrong password")
