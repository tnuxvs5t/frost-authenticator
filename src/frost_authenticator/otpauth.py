from __future__ import annotations

from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

from .models import Account
from .totp import SUPPORTED_ALGORITHMS, normalize_secret


class OTPAuthError(ValueError):
    """Raised when an otpauth:// URI cannot be parsed."""


def _first(params: dict[str, list[str]], name: str, default: str = "") -> str:
    values = params.get(name)
    if not values:
        return default
    return values[0]


def parse_otpauth_uri(uri: str) -> Account:
    uri = uri.strip()
    parsed = urlparse(uri)
    if parsed.scheme.lower() != "otpauth":
        raise OTPAuthError("URI must start with otpauth://")
    if parsed.netloc.lower() != "totp":
        raise OTPAuthError("Only otpauth://totp/... accounts are supported")

    params = parse_qs(parsed.query)
    raw_secret = _first(params, "secret")
    if not raw_secret:
        raise OTPAuthError("Missing secret parameter")
    secret = normalize_secret(raw_secret)

    label = unquote(parsed.path.lstrip("/"))
    label_issuer = ""
    label_account = label
    if ":" in label:
        label_issuer, label_account = label.split(":", 1)

    issuer = _first(params, "issuer", label_issuer).strip()
    account_name = label_account.strip()
    if not account_name and label and not label_issuer:
        account_name = label.strip()

    algorithm = _first(params, "algorithm", "SHA1").upper()
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise OTPAuthError(f"Unsupported algorithm: {algorithm}")

    try:
        digits = int(_first(params, "digits", "6"))
        period = int(_first(params, "period", "30"))
    except ValueError as exc:
        raise OTPAuthError("digits and period must be integers") from exc

    try:
        return Account(
            issuer=issuer,
            account=account_name,
            secret=secret,
            digits=digits,
            period=period,
            algorithm=algorithm,
        )
    except Exception as exc:
        raise OTPAuthError(str(exc)) from exc


def build_otpauth_uri(account: Account) -> str:
    label = quote(f"{account.issuer}:{account.account}" if account.issuer else account.account)
    params = {
        "secret": account.secret,
        "issuer": account.issuer,
        "algorithm": account.algorithm,
        "digits": str(account.digits),
        "period": str(account.period),
    }
    params = {k: v for k, v in params.items() if v != ""}
    return f"otpauth://totp/{label}?{urlencode(params)}"
