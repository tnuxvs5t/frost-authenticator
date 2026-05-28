from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QPushButton  # noqa: E402

from frost_authenticator.app import MainWindow  # noqa: E402
from frost_authenticator.vault import VaultStore  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_add_button_does_not_pass_checked_bool_as_import_preset() -> None:
    app = _app()
    assert app is not None
    with TemporaryDirectory() as d:
        store = VaultStore(Path(d) / "vault.json")
        store.save([], password="correct horse battery staple", create_new=True)
        window = MainWindow(store, "correct horse battery staple", [])
        calls: list[object] = []

        def fake_add_account(preset=None):  # type: ignore[no-untyped-def]
            calls.append(preset)

        window.add_account = fake_add_account  # type: ignore[method-assign]
        add_buttons = [button for button in window.findChildren(QPushButton) if button.text() == "＋ 添加"]
        assert add_buttons

        add_buttons[0].click()

        assert calls == [None]
