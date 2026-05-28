from frost_authenticator.totp import hotp, normalize_secret, seconds_remaining, totp

RFC4226_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


def test_hotp_rfc4226_vectors() -> None:
    expected = ["755224", "287082", "359152", "969429", "338314", "254676", "287922", "162583", "399871", "520489"]
    for counter, code in enumerate(expected):
        assert hotp(RFC4226_SECRET, counter) == code


def test_totp_rfc6238_sha1_vectors() -> None:
    vectors = [
        (59, "94287082"),
        (1111111109, "07081804"),
        (1111111111, "14050471"),
        (1234567890, "89005924"),
        (2000000000, "69279037"),
        (20000000000, "65353130"),
    ]
    for timestamp, code in vectors:
        assert totp(RFC4226_SECRET, timestamp=timestamp, digits=8, period=30, algorithm="SHA1") == code


def test_normalize_accepts_grouping() -> None:
    assert normalize_secret("gez dgnbv-gy3tqojq====") == "GEZDGNBVGY3TQOJQ"


def test_seconds_remaining_boundary() -> None:
    assert seconds_remaining(timestamp=0, period=30) == 30
    assert seconds_remaining(timestamp=29, period=30) == 1
