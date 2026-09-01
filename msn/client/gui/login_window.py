"""
MSN Messenger Login Window (Windows Live Messenger Authenticator)
Classic login screen with avatar selector, status picker, credentials, and animated connecting state.
"""
import os
import json
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QFrame, QWidget, QScrollArea
)
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QPen, QCursor, QIcon

from msn.common.protocol import UserProfile, UserStatus
from msn.client.emoticons import AVATAR_PRESETS, generate_avatar_pixmap
from msn.client.audio import MSNAudioManager
from msn.client.gui.register_dialog import MSNRegisterDialog
from msn.client.gui.options_dialog import MSNOptionsDialog, load_app_settings, save_app_settings


class MSNLoginWindow(QDialog):
    sig_login_requested = pyqtSignal(str, str, str, UserStatus, str, str, str)  # email, password, nick, status, avatar_id, personal_msg, server_address
    sig_register_requested = pyqtSignal(str, str, str, str, str)  # email, password, nickname, avatar_id, personal_msg

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Windows Live Messenger")
        self.setMinimumSize(420, 640)
        self.resize(430, 670)

        # Set window icon to logo.png
        possible_logo_paths = [
            os.path.abspath("logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logo.png"),
        ]
        logo_file = next((p for p in possible_logo_paths if os.path.exists(p)), None)
        if logo_file:
            self.setWindowIcon(QIcon(logo_file))

        self.selected_avatar_id = "avatar_1"
        self.audio = MSNAudioManager.get_instance()
        self.register_dialog: Optional[MSNRegisterDialog] = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header Frame with MSN Logo
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Logo Icon
        logo_lbl = QLabel("🦋")
        logo_lbl.setFont(QFont("Segoe UI Emoji", 34))
        header_layout.addWidget(logo_lbl)

        title_layout = QVBoxLayout()
        title_lbl = QLabel("<b>Windows Live</b>")
        title_lbl.setStyleSheet("font-size: 22px; color: #0072c6; font-weight: bold;")
        subtitle_lbl = QLabel("Messenger")
        subtitle_lbl.setStyleSheet("font-size: 15px; color: #418ab3;")
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(subtitle_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addWidget(header_widget)

        # Avatar Selection Area
        avatar_box = QHBoxLayout()
        avatar_box.addStretch()

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=74))
        self.avatar_lbl.setFixedSize(78, 78)
        self.avatar_lbl.setStyleSheet("border: 2px solid #a3c8e5; border-radius: 12px; background: white;")
        avatar_box.addWidget(self.avatar_lbl)

        # Avatar Switcher Button
        self.change_avatar_btn = QPushButton("Mudar...")
        self.change_avatar_btn.setFixedHeight(30)
        self.change_avatar_btn.setFixedWidth(74)
        self.change_avatar_btn.clicked.connect(self._cycle_avatar)
        avatar_box.addWidget(self.change_avatar_btn)

        avatar_box.addStretch()
        main_layout.addLayout(avatar_box)

        # Inputs Form Frame
        form_frame = QFrame()
        form_frame.setObjectName("HeaderFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        # Email Input
        email_lbl = QLabel("Endereço de início de sessão:")
        email_lbl.setStyleSheet("font-size: 12px; color: #2c3e50; font-weight: bold;")
        self.email_input = QLineEdit()
        self.email_input.setFixedHeight(34)
        self.email_input.setPlaceholderText("exemplo@hotmail.com ou @live.com")
        self.email_input.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        form_layout.addWidget(email_lbl)
        form_layout.addWidget(self.email_input)

        # Password Input
        pass_lbl = QLabel("Palavra-passe:")
        pass_lbl.setStyleSheet("font-size: 12px; color: #2c3e50; font-weight: bold;")
        
        pass_box = QHBoxLayout()
        pass_box.setContentsMargins(0, 0, 0, 0)
        pass_box.setSpacing(4)

        self.pass_input = QLineEdit()
        self.pass_input.setFixedHeight(34)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("••••••••")
        self.pass_input.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        pass_box.addWidget(self.pass_input)

        self.show_pass_btn = QPushButton("👁️")
        self.show_pass_btn.setFixedSize(36, 34)
        self.show_pass_btn.setToolTip("Mostrar / Ocultar palavra-passe")
        self.show_pass_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.show_pass_btn.clicked.connect(self._toggle_password_visibility)
        pass_box.addWidget(self.show_pass_btn)

        form_layout.addWidget(pass_lbl)
        form_layout.addLayout(pass_box)

        # Status Selector at Login
        status_lbl = QLabel("Estado inicial:")
        status_lbl.setStyleSheet("font-size: 12px; color: #2c3e50; font-weight: bold;")
        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(34)
        self.status_combo.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        for status in [UserStatus.ONLINE, UserStatus.BUSY, UserStatus.AWAY, UserStatus.INVISIBLE]:
            self.status_combo.addItem(f"{status.icon_char} {status.label_pt}", status)
        form_layout.addWidget(status_lbl)
        form_layout.addWidget(self.status_combo)

        # Allow pressing Enter to trigger login
        self.email_input.returnPressed.connect(self._on_sign_in_clicked)
        self.pass_input.returnPressed.connect(self._on_sign_in_clicked)

        main_layout.addWidget(form_frame)

        # Forgot Password / Reset Link
        self.forgot_pass_btn = QPushButton("🔑 Esqueceu-se da palavra-passe? Redefinir aqui")
        self.forgot_pass_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #557a95;
                font-size: 11px;
                text-align: right;
                padding: 2px;
            }
            QPushButton:hover {
                color: #0072c6;
                text-decoration: underline;
            }
        """)
        self.forgot_pass_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.forgot_pass_btn.clicked.connect(self._open_reset_password_dialog)
        main_layout.addWidget(self.forgot_pass_btn)

        # Register New Account Link / Button
        self.register_link_btn = QPushButton("✨ Não tem conta? Criar uma conta do Windows Live ID")
        self.register_link_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #0072c6;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                padding: 6px;
            }
            QPushButton:hover {
                color: #005a9e;
                text-decoration: underline;
            }
        """)
        self.register_link_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.register_link_btn.clicked.connect(self._open_register_dialog)
        main_layout.addWidget(self.register_link_btn)

        # Options Checkboxes
        self.remember_id_cb = QCheckBox("Lembrar o meu ID / endereço de email")
        self.remember_id_cb.setStyleSheet("font-size: 12px; color: #34495e;")
        main_layout.addWidget(self.remember_id_cb)

        self.remember_pass_cb = QCheckBox("Lembrar a minha palavra-passe")
        self.remember_pass_cb.setStyleSheet("font-size: 12px; color: #34495e;")
        main_layout.addWidget(self.remember_pass_cb)

        self.auto_login_cb = QCheckBox("Iniciar sessão automaticamente")
        self.auto_login_cb.setStyleSheet("font-size: 12px; color: #34495e;")
        main_layout.addWidget(self.auto_login_cb)

        # Settings / Options Button
        self.options_btn = QPushButton("⚙️ Opções e Definições...")
        self.options_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #0072c6;
                font-size: 11px;
                text-align: left;
                padding: 4px 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #005a9e;
                text-decoration: underline;
            }
        """)
        self.options_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.options_btn.clicked.connect(self._open_options_dialog)
        main_layout.addWidget(self.options_btn)

        self.server_host_input = QLineEdit("127.0.0.1:8800")
        self.server_host_input.hide()

        # Status / Connecting Message
        self.connecting_lbl = QLabel("")
        self.connecting_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connecting_lbl.setStyleSheet("color: #0072c6; font-weight: bold; font-size: 12px;")
        self.connecting_lbl.hide()
        main_layout.addWidget(self.connecting_lbl)

        # Sign In Button
        self.sign_in_btn = QPushButton("Iniciar Sessão")
        self.sign_in_btn.setObjectName("PrimaryBtn")
        self.sign_in_btn.setFixedHeight(42)
        self.sign_in_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sign_in_btn.clicked.connect(self._on_sign_in_clicked)
        main_layout.addWidget(self.sign_in_btn)

        # Protection timeout
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)

        # Load remembered credentials
        self._load_saved_prefs()

    def _open_register_dialog(self):
        self.register_dialog = MSNRegisterDialog(self)
        self.register_dialog.sig_register_requested.connect(self._on_register_submitted)
        if self.register_dialog.exec():
            # Pre-fill email and password from registration
            self.email_input.setText(self.register_dialog.email_input.text().strip())
            self.pass_input.setText(self.register_dialog.pass_input.text())
            self.selected_avatar_id = self.register_dialog.selected_avatar_id
            self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=74))
            
            # Auto sign in immediately!
            QTimer.singleShot(150, self._on_sign_in_clicked)

    def _on_register_submitted(self, email: str, pwd: str, nick: str, avatar_id: str, personal_msg: str):
        self.sig_register_requested.emit(email, pwd, nick, avatar_id, personal_msg)

    def handle_register_response(self, success: bool, message: str):
        if self.register_dialog:
            self.register_dialog.on_register_result(success, message)

    def _toggle_server_settings(self):
        self.server_settings_frame.setVisible(not self.server_settings_frame.isVisible())

    def _toggle_password_visibility(self):
        if self.pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pass_btn.setText("🙈")
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pass_btn.setText("👁️")

    def _open_reset_password_dialog(self):
        from PyQt6.QtWidgets import QInputDialog
        email = self.email_input.text().strip().lower()
        if not email or "@" not in email:
            email, ok = QInputDialog.getText(self, "Redefinir Palavra-passe", "Introduz o teu endereço de email:")
            if not ok or not email:
                return
            email = email.strip().lower()

        new_pass, ok2 = QInputDialog.getText(
            self, "Nova Palavra-passe", f"Introduz a nova palavra-passe para {email}:",
            QLineEdit.EchoMode.Normal
        )
        if not ok2 or not new_pass:
            return

        if len(new_pass) < 4:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Aviso", "A palavra-passe deve ter pelo menos 4 caracteres.")
            return

        # Direct database reset and network notification
        try:
            from msn.server.database import MSNDatabase
            db = MSNDatabase()
            ok_res, msg = db.reset_password(email, new_pass)
            if ok_res:
                self.email_input.setText(email)
                self.pass_input.setText(new_pass)
                self.connecting_lbl.setText("✅ Palavra-passe redefinida! A entrar...")
                self.connecting_lbl.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
                self.connecting_lbl.show()
                QTimer.singleShot(200, self._on_sign_in_clicked)
        except Exception as e:
            self.connecting_lbl.setText(f"❌ Erro ao redefinir: {str(e)}")
            self.connecting_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 12px;")

    def _cycle_avatar(self):
        keys = list(AVATAR_PRESETS.keys())
        idx = (keys.index(self.selected_avatar_id) + 1) % len(keys)
        self.selected_avatar_id = keys[idx]
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=74))

    def _open_options_dialog(self):
        dlg = MSNOptionsDialog(self)
        dlg.sig_settings_updated.connect(self._on_settings_updated)
        dlg.exec()

    def _on_settings_updated(self, settings: dict):
        self._load_saved_prefs()

    def _load_saved_prefs(self):
        data = load_app_settings()

        remember_email = data.get("remember_email", True)
        remember_pass = data.get("remember_password", False)
        auto_login = data.get("auto_login", False)

        self.remember_id_cb.setChecked(remember_email)
        self.remember_pass_cb.setChecked(remember_pass)
        self.auto_login_cb.setChecked(auto_login)

        if remember_email and data.get("saved_email"):
            self.email_input.setText(data["saved_email"])

        if remember_pass and data.get("saved_password"):
            self.pass_input.setText(data["saved_password"])
        else:
            self.pass_input.clear()

        if "avatar_id" in data:
            self.selected_avatar_id = data["avatar_id"]
            self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=74))

        if "server_address" in data:
            self.server_host_input.setText(data["server_address"])

        # If auto-login is active and email exists, trigger auto-sign in
        if auto_login and self.email_input.text() and self.pass_input.text():
            QTimer.singleShot(400, self._on_sign_in_clicked)

    def _save_prefs(self, email: str, password: str):
        settings = load_app_settings()
        settings["remember_email"] = self.remember_id_cb.isChecked()
        settings["remember_password"] = self.remember_pass_cb.isChecked()
        settings["auto_login"] = self.auto_login_cb.isChecked()
        settings["avatar_id"] = self.selected_avatar_id
        settings["server_address"] = self.server_host_input.text().strip() or "127.0.0.1:8800"

        if self.remember_id_cb.isChecked():
            settings["saved_email"] = email
        else:
            settings["saved_email"] = ""

        if self.remember_pass_cb.isChecked():
            settings["saved_password"] = password
        else:
            settings["saved_password"] = ""

        save_app_settings(settings)

    def _on_sign_in_clicked(self):
        email = self.email_input.text().strip().lower()
        if not email or "@" not in email:
            self.email_input.setFocus()
            self.connecting_lbl.setText("❌ Insere um email válido (ex: utilizador@hotmail.com)")
            self.connecting_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
            self.connecting_lbl.show()
            return

        pwd = self.pass_input.text()
        nick = email.split("@")[0]
        status = self.status_combo.currentData() or UserStatus.ONLINE

        self._save_prefs(email, pwd)

        self.sign_in_btn.setEnabled(False)
        self.connecting_lbl.setText("🔄 A iniciar sessão no Windows Live Messenger...")
        self.connecting_lbl.setStyleSheet("color: #0072c6; font-weight: bold; font-size: 12px;")
        self.connecting_lbl.show()
        self.timeout_timer.start(6000)

        server_addr = self.server_host_input.text().strip() or "127.0.0.1:8800"

        self.sig_login_requested.emit(
            email,
            pwd,
            nick,
            status,
            self.selected_avatar_id,
            "A ouvir: 🎵 Música dos anos 2000",
            server_addr
        )

    def _on_timeout(self):
        self.sign_in_btn.setEnabled(True)
        self.connecting_lbl.setText("⚠️ O servidor demorou a responder. Clica novamente em 'Iniciar Sessão'.")
        self.connecting_lbl.setStyleSheet("color: #d35400; font-weight: bold; font-size: 11px;")

    def on_login_failed(self, error_msg: str):
        self.timeout_timer.stop()
        self.sign_in_btn.setEnabled(True)
        self.connecting_lbl.setText(f"❌ {error_msg}")
        self.connecting_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
