from __future__ import annotations

from pathlib import Path


class QRDecodeError(RuntimeError):
    """Raised when a QR image cannot be decoded."""


def decode_qr_image(path: str | Path) -> str:
    """Decode the first QR code found in an image using OpenCV.

    The OpenCV import is intentionally lazy so the rest of the app can still be
    imported in minimal/test environments.
    """
    try:
        import cv2  # type: ignore
    except Exception as exc:
        raise QRDecodeError("QR import requires opencv-python-headless in the venv.") from exc

    image_path = str(path)
    image = cv2.imread(image_path)
    if image is None:
        raise QRDecodeError("Cannot read image file.")

    detector = cv2.QRCodeDetector()
    data, _points, _straight = detector.detectAndDecode(image)
    if not data:
        # OpenCV has a multi-QR path on newer versions; try it before giving up.
        try:
            ok, decoded, _points, _straight = detector.detectAndDecodeMulti(image)
        except Exception:
            ok, decoded = False, []
        if ok and decoded:
            data = next((item for item in decoded if item), "")

    if not data:
        raise QRDecodeError("No QR code was decoded from this image.")
    return data.strip()
