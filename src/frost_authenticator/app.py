from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import APP_ID, APP_NAME
from .models import Account
from .otpauth import OTPAuthError, parse_otpauth_uri
from .qr import QRDecodeError, decode_qr_image
from .totp import SUPPORTED_ALGORITHMS, TOTPError, preview, totp
from .vault import VaultError, VaultStore


CODE_FONT = QFont("monospace", 18, QFont.Weight.Bold)
TEXT_FONT = QFont("sans", 10)


class SetupVaultDialog(QDialog):
    def __init__(self, vault_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("创建加密保险库")
        self.setMinimumWidth(460)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.error = QLabel("")
        self.error.setObjectName("errorLabel")
        self.error.setWordWrap(True)

        form = QFormLayout()
        form.addRow("主密码", self.password)
        form.addRow("确认密码", self.confirm)
        form.addRow("保存位置", QLabel(str(vault_path)))

        hint = QLabel("主密码只保存在你的脑袋里。忘记后无法恢复这些 TOTP 密钥。")
        hint.setWordWrap(True)

        buttons = QHBoxLayout()
        ok = QPushButton("创建")
        cancel = QPushButton("退出")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("首次运行：先冻结一个本地加密保险库。"))
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addWidget(self.error)
        layout.addLayout(buttons)

    def accept(self) -> None:  # noqa: D401 - Qt override
        pw = self.password.text()
        if len(pw) < 8:
            self.error.setText("主密码至少 8 个字符。")
            return
        if pw != self.confirm.text():
            self.error.setText("两次输入的密码不一致。")
            return
        super().accept()

    def value(self) -> str:
        return self.password.text()


class UnlockVaultDialog(QDialog):
    def __init__(self, vault_path: Path, error_text: str = "") -> None:
        super().__init__()
        self.setWindowTitle("解锁 Frost Authenticator")
        self.setMinimumWidth(430)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.accept)
        self.error = QLabel(error_text)
        self.error.setObjectName("errorLabel")
        self.error.setWordWrap(True)

        form = QFormLayout()
        form.addRow("主密码", self.password)
        form.addRow("保险库", QLabel(str(vault_path)))

        buttons = QHBoxLayout()
        ok = QPushButton("解锁")
        cancel = QPushButton("退出")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("输入主密码解锁本机验证码。"))
        layout.addLayout(form)
        layout.addWidget(self.error)
        layout.addLayout(buttons)

    def value(self) -> str:
        return self.password.text()


class AccountDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, account: Account | None = None) -> None:
        super().__init__(parent)
        self._original = account
        self.result_account: Account | None = None
        self.setWindowTitle("编辑账号" if account else "添加账号")
        self.setMinimumWidth(560)

        self.uri = QLineEdit()
        self.uri.setPlaceholderText("otpauth://totp/...  可留空，也可从剪贴板解析")
        self.issuer = QLineEdit()
        self.account = QLineEdit()
        self.secret = QLineEdit()
        self.secret.setPlaceholderText("Base32 密钥，例如 JBSWY3DPEHPK3PXP")
        self.secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_secret = QCheckBox("显示")
        self.show_secret.toggled.connect(self._toggle_secret)
        secret_row = QHBoxLayout()
        secret_row.addWidget(self.secret, 1)
        secret_row.addWidget(self.show_secret)

        self.algorithm = QComboBox()
        self.algorithm.addItems(SUPPORTED_ALGORITHMS)
        self.digits = QComboBox()
        self.digits.addItems(["6", "7", "8"])
        self.period = QSpinBox()
        self.period.setRange(10, 300)
        self.period.setValue(30)
        self.period.setSuffix(" 秒")
        self.preview = QLabel("预览：—")
        self.preview.setObjectName("previewLabel")
        self.error = QLabel("")
        self.error.setObjectName("errorLabel")
        self.error.setWordWrap(True)

        parse_button = QPushButton("解析 URI/剪贴板")
        parse_button.clicked.connect(self.parse_uri)
        uri_row = QHBoxLayout()
        uri_row.addWidget(self.uri, 1)
        uri_row.addWidget(parse_button)

        form = QFormLayout()
        form.addRow("otpauth URI", uri_row)
        form.addRow("服务/Issuer", self.issuer)
        form.addRow("账号/Account", self.account)
        form.addRow("Base32 密钥", secret_row)
        form.addRow("算法", self.algorithm)
        form.addRow("位数", self.digits)
        form.addRow("周期", self.period)

        buttons = QHBoxLayout()
        ok = QPushButton("保存")
        cancel = QPushButton("取消")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.preview)
        layout.addWidget(self.error)
        layout.addLayout(buttons)

        for widget in (self.issuer, self.account, self.secret):
            widget.textChanged.connect(self.update_preview)
        self.algorithm.currentTextChanged.connect(self.update_preview)
        self.digits.currentTextChanged.connect(self.update_preview)
        self.period.valueChanged.connect(self.update_preview)

        if account:
            self.populate(account)

    def _toggle_secret(self, checked: bool) -> None:
        self.secret.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def populate(self, account: Account) -> None:
        self.issuer.setText(account.issuer)
        self.account.setText(account.account)
        self.secret.setText(account.secret)
        self.algorithm.setCurrentText(account.algorithm)
        self.digits.setCurrentText(str(account.digits))
        self.period.setValue(account.period)
        self.update_preview()

    def parse_uri(self) -> None:
        text = self.uri.text().strip() or QApplication.clipboard().text().strip()
        if not text:
            self.error.setText("没有可解析的 otpauth:// URI。")
            return
        try:
            parsed = parse_otpauth_uri(text)
        except OTPAuthError as exc:
            self.error.setText(str(exc))
            return
        self.populate(parsed)
        self.uri.setText(text)
        self.error.setText("已从 URI 填充。")

    def _make_account(self) -> Account:
        original = self._original
        kwargs = {
            "issuer": self.issuer.text(),
            "account": self.account.text(),
            "secret": self.secret.text(),
            "algorithm": self.algorithm.currentText(),
            "digits": int(self.digits.currentText()),
            "period": int(self.period.value()),
            "updated_at": int(time.time()),
        }
        if original:
            kwargs["id"] = original.id
            kwargs["created_at"] = original.created_at
        return Account(**kwargs)  # type: ignore[arg-type]

    def update_preview(self) -> None:
        try:
            account = self._make_account()
            p = preview(account.secret, period=account.period, digits=account.digits, algorithm=account.algorithm)
            self.preview.setText(f"预览：{format_code(p.code)}   剩余 {p.remaining}s")
        except Exception:
            self.preview.setText("预览：—")

    def accept(self) -> None:  # noqa: D401 - Qt override
        try:
            self.result_account = self._make_account()
        except Exception as exc:
            self.error.setText(str(exc))
            return
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self, store: VaultStore, password: str, accounts: list[Account]) -> None:
        super().__init__()
        self.store = store
        self.password = password
        self.accounts = accounts
        self._clipboard_timers: list[QTimer] = []
        self.setWindowTitle(APP_NAME)
        self.resize(980, 580)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索服务或账号…")
        self.search.textChanged.connect(self.render_table)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["服务", "账号", "验证码", "剩余", "复制", "编辑", "删除"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        add_button = QPushButton("＋ 添加")
        # QPushButton.clicked and QAction.triggered pass a boolean ``checked``
        # argument.  ``add_account`` also accepts an Account preset for imports,
        # so connecting it directly makes that boolean look like a preset and
        # crashes on ``dialog.populate(False)``.  Keep the UI action argument out
        # of the application path.
        add_button.clicked.connect(lambda _checked=False: self.add_account())
        qr_button = QPushButton("从二维码图片导入")
        qr_button.clicked.connect(self.import_qr)
        uri_button = QPushButton("从剪贴板 URI 导入")
        uri_button.clicked.connect(self.import_uri_from_clipboard)

        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(uri_button)
        top.addWidget(qr_button)
        top.addWidget(add_button)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        self.setCentralWidget(central)

        self._build_menu()
        self.statusBar().showMessage(f"保险库：{self.store.path}")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.render_table)
        self.timer.start(1000)
        self.render_table()

    def _build_menu(self) -> None:
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_action = QAction("添加", self)
        add_action.triggered.connect(lambda _checked=False: self.add_account())
        toolbar.addAction(add_action)

        lock_action = QAction("锁定并退出", self)
        lock_action.triggered.connect(self.close)
        toolbar.addAction(lock_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def filtered_accounts(self) -> list[Account]:
        query = self.search.text().strip().lower()
        sorted_accounts = sorted(self.accounts, key=lambda a: ((a.issuer or "").lower(), (a.account or "").lower()))
        if not query:
            return sorted_accounts
        return [a for a in sorted_accounts if query in a.issuer.lower() or query in a.account.lower()]

    def render_table(self) -> None:
        accounts = self.filtered_accounts()
        self.table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            self._set_text(row, 0, account.issuer or "—")
            self._set_text(row, 1, account.account or "—")
            try:
                p = preview(account.secret, period=account.period, digits=account.digits, algorithm=account.algorithm)
                code_text = format_code(p.code)
                remaining_text = f"{p.remaining}s / {p.period}s"
            except (TOTPError, ValueError) as exc:
                code_text = "错误"
                remaining_text = str(exc)

            code_item = self._set_text(row, 2, code_text)
            code_item.setFont(CODE_FONT)
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if code_text != "错误":
                code_item.setForeground(QBrush(QColor("#0b5cad")))

            remaining_item = self._set_text(row, 3, remaining_text)
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if remaining_text.startswith(("1s", "2s", "3s", "4s", "5s")):
                remaining_item.setForeground(QBrush(QColor("#b00020")))

            self._set_button(row, 4, "复制", lambda _=False, account_id=account.id: self.copy_code(account_id))
            self._set_button(row, 5, "编辑", lambda _=False, account_id=account.id: self.edit_account(account_id))
            self._set_button(row, 6, "删除", lambda _=False, account_id=account.id: self.delete_account(account_id))

        if not accounts:
            self.statusBar().showMessage("没有匹配账号。点击“添加”或导入 otpauth URI/二维码。")

    def _set_text(self, row: int, column: int, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFont(TEXT_FONT)
        item.setToolTip(text)
        self.table.setItem(row, column, item)
        return item

    def _set_button(self, row: int, column: int, text: str, slot: Callable[..., None]) -> None:
        button = QPushButton(text)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.clicked.connect(slot)
        self.table.setCellWidget(row, column, button)

    def find_account_index(self, account_id: str) -> int | None:
        for idx, account in enumerate(self.accounts):
            if account.id == account_id:
                return idx
        return None

    def save_accounts(self) -> bool:
        try:
            self.store.save(self.accounts, self.password)
        except VaultError as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return False
        self.statusBar().showMessage("已保存。", 2500)
        return True

    def add_account(self, preset: Account | None = None) -> None:
        dialog = AccountDialog(self)
        if preset is not None:
            dialog.populate(preset)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.result_account is None:
            return
        new_account = dialog.result_account
        self.accounts.append(new_account)
        if self.save_accounts():
            self.render_table()

    def edit_account(self, account_id: str) -> None:
        idx = self.find_account_index(account_id)
        if idx is None:
            return
        dialog = AccountDialog(self, self.accounts[idx])
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.result_account is None:
            return
        self.accounts[idx] = dialog.result_account
        if self.save_accounts():
            self.render_table()

    def delete_account(self, account_id: str) -> None:
        idx = self.find_account_index(account_id)
        if idx is None:
            return
        account = self.accounts[idx]
        answer = QMessageBox.question(
            self,
            "删除账号",
            f"确定删除 {account.title} 吗？这个操作只会删除本地副本。",
            QMessageBox.StandardButton.Delete | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Delete:
            return
        del self.accounts[idx]
        if self.save_accounts():
            self.render_table()

    def import_uri_from_clipboard(self) -> None:
        text = QApplication.clipboard().text().strip()
        if not text:
            QMessageBox.information(self, "剪贴板为空", "剪贴板里没有 otpauth:// URI。")
            return
        try:
            account = parse_otpauth_uri(text)
        except OTPAuthError as exc:
            QMessageBox.warning(self, "URI 无法解析", str(exc))
            return
        self.add_account(account)

    def import_qr(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择二维码图片",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All files (*)",
        )
        if not path:
            return
        try:
            text = decode_qr_image(path)
            account = parse_otpauth_uri(text)
        except (QRDecodeError, OTPAuthError) as exc:
            QMessageBox.warning(self, "二维码无法导入", str(exc))
            return
        self.add_account(account)

    def copy_code(self, account_id: str) -> None:
        idx = self.find_account_index(account_id)
        if idx is None:
            return
        account = self.accounts[idx]
        try:
            code = totp(account.secret, period=account.period, digits=account.digits, algorithm=account.algorithm)
        except Exception as exc:
            QMessageBox.warning(self, "验证码错误", str(exc))
            return
        QApplication.clipboard().setText(code)
        self.statusBar().showMessage(f"已复制 {account.title} 的验证码；30 秒后尝试清空剪贴板。", 3000)
        QTimer.singleShot(30_000, lambda copied=code: self.clear_clipboard_if_same(copied))

    def clear_clipboard_if_same(self, copied: str) -> None:
        clipboard = QApplication.clipboard()
        if clipboard.text() == copied:
            clipboard.clear()

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "关于 Frost Authenticator",
            (
                "Frost Authenticator\n\n"
                "本地加密 TOTP 验证器：PyQt6 界面、PBKDF2 + Fernet 加密保险库、"
                "otpauth URI 与二维码图片导入。\n\n"
                "冰冷边界：它保护本地存储，不替代系统全盘加密；忘记主密码无法恢复。"
            ),
        )


def format_code(code: str) -> str:
    if len(code) == 6:
        return f"{code[:3]} {code[3:]}"
    if len(code) == 8:
        return f"{code[:4]} {code[4:]}"
    return code


def icon_path() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "frost-authenticator.svg"


def apply_style(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QMainWindow, QDialog { background: #f5fbff; }
        QLineEdit, QComboBox, QSpinBox, QTableWidget {
            background: white; border: 1px solid #b8d7ef; border-radius: 6px; padding: 4px;
        }
        QPushButton {
            background: #dff3ff; border: 1px solid #7bbce1; border-radius: 7px; padding: 6px 10px;
        }
        QPushButton:hover { background: #c9ecff; }
        QPushButton:pressed { background: #aee1ff; }
        QToolBar { background: #e9f7ff; border-bottom: 1px solid #c7e5f8; spacing: 8px; padding: 4px; }
        QHeaderView::section { background: #dff3ff; border: 0; border-right: 1px solid #b8d7ef; padding: 6px; }
        QLabel#errorLabel { color: #b00020; }
        QLabel#previewLabel { color: #0b5cad; font-weight: 600; }
        QStatusBar { background: #e9f7ff; }
        """
    )


def unlock_or_create(store: VaultStore) -> tuple[str, list[Account]] | None:
    if not store.exists():
        dialog = SetupVaultDialog(store.path)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        password = dialog.value()
        try:
            accounts = store.create(password)
        except VaultError as exc:
            QMessageBox.critical(None, "创建保险库失败", str(exc))
            return None
        return password, accounts

    error = ""
    while True:
        dialog = UnlockVaultDialog(store.path, error)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        password = dialog.value()
        try:
            return password, store.load(password)
        except VaultError as exc:
            error = str(exc)


def main(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ID)
    ico = icon_path()
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))
    apply_style(app)

    store = VaultStore()
    unlocked = unlock_or_create(store)
    if unlocked is None:
        return 0
    password, accounts = unlocked
    window = MainWindow(store, password, accounts)
    if ico.exists():
        window.setWindowIcon(QIcon(str(ico)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
