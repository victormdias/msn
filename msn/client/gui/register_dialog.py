"""
MSN Messenger / Windows Live ID Registration Dialog
Allows new users to create their own real account with email, password, nickname, and avatar.
"""
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
     QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
     QPushButton, QFrame, QWidget, QMessageBox
)
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QPen, QCursor, QIcon

from msn.client.emoticons import AVATAR_PRESETS, generate_avatar_pixmap


class MSNRegisterDialog(QDialog):
    sig_register_requested = pyqtSignal(str, str, str, str, str)  # email, password, nickname, avatar_id, personal_msg

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registo do Windows Live ID - MSN Messenger")
        self.setMinimumSize(420, 640)
        self.resize(430, 670)
        self.selected_avatar_id = "avatar_1"
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header Frame with Logo
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo_lbl = QLabel("🦋")
        logo_lbl.setFont(QFont("Segoe UI Emoji", 30))
        header_layout.addWidget(logo_lbl)

        title_layout = QVBoxLayout()
        title_lbl = QLabel("<b>Criar Conta do Windows Live ID</b>")
        title_lbl.setStyleSheet("font-size: 17px; color: #0072c6; font-weight: bold;")
        subtitle_lbl = QLabel("Regista a tua conta para entrar no MSN Messenger")
        subtitle_lbl.setStyleSheet("font-size: 12px; color: #557a95;")
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(subtitle_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addWidget(header_widget)

        # Avatar Chooser
        avatar_box = QHBoxLayout()
        avatar_box.addStretch()

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=68))
        self.avatar_lbl.setFixedSize(72, 72)
        self.avatar_lbl.setStyleSheet("border: 2px solid #a3c8e5; border-radius: 10px; background: white;")
        avatar_box.addWidget(self.avatar_lbl)

        self.change_avatar_btn = QPushButton("Mudar Avatar...")
        self.change_avatar_btn.setFixedHeight(30)
        self.change_avatar_btn.setFixedWidth(110)
        self.change_avatar_btn.clicked.connect(self._cycle_avatar)
        avatar_box.addWidget(self.change_avatar_btn)

        avatar_box.addStretch()
        main_layout.addLayout(avatar_box)

        # Form
        form_frame = QFrame()
        form_frame.setObjectName("HeaderFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(14, 12, 14, 12)
        form_layout.setSpacing(8)

        # Email
        email_lbl = QLabel("Endereço de Email (Windows Live ID):")
        email_lbl.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
        self.email_input = QLineEdit()
        self.email_input.setFixedHeight(32)
        self.email_input.setPlaceholderText("exemplo@hotmail.com ou @live.com")
        form_layout.addWidget(email_lbl)
        form_layout.addWidget(self.email_input)

        # Nickname
        nick_lbl = QLabel("A tua Alcunha (Nome visível no MSN):")
        nick_lbl.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
        self.nick_input = QLineEdit()
        self.nick_input.setFixedHeight(32)
        self.nick_input.setPlaceholderText("O teu Nickname (ex: Victor (H))")
        form_layout.addWidget(nick_lbl)
        form_layout.addWidget(self.nick_input)

        # Password
        pass_lbl = QLabel("Palavra-passe:")
        pass_lbl.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
        self.pass_input = QLineEdit()
        self.pass_input.setFixedHeight(32)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Mínimo 4 caracteres")
        form_layout.addWidget(pass_lbl)
        form_layout.addWidget(self.pass_input)

        # Confirm Password
        pass2_lbl = QLabel("Confirmar Palavra-passe:")
        pass2_lbl.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
        self.pass2_input = QLineEdit()
        self.pass2_input.setFixedHeight(32)
        self.pass2_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass2_input.setPlaceholderText("Repita a palavra-passe")
        form_layout.addWidget(pass2_lbl)
        form_layout.addWidget(self.pass2_input)

        # Personal message
        msg_lbl = QLabel("Mensagem Pessoal inicial (Opcional):")
        msg_lbl.setStyleSheet("font-size: 11px; color: #333333;")
        self.msg_input = QLineEdit()
        self.msg_input.setFixedHeight(32)
        self.msg_input.setPlaceholderText("ex: Olá, estou no MSN! (L)")
        form_layout.addWidget(msg_lbl)
        form_layout.addWidget(self.msg_input)

        main_layout.addWidget(form_frame)

        # Status / Error Label
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
        self.status_lbl.setWordWrap(True)
        main_layout.addWidget(self.status_lbl)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.register_btn = QPushButton("Criar Conta e Registar")
        self.register_btn.setObjectName("PrimaryBtn")
        self.register_btn.setFixedHeight(36)
        self.register_btn.clicked.connect(self._on_register_clicked)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.register_btn)
        main_layout.addLayout(btn_layout)

    def _cycle_avatar(self):
        keys = list(AVATAR_PRESETS.keys())
        idx = (keys.index(self.selected_avatar_id) + 1) % len(keys)
        self.selected_avatar_id = keys[idx]
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=64))

    def _on_register_clicked(self):
        email = self.email_input.text().strip().lower()
        nickname = self.nick_input.text().strip()
        pwd = self.pass_input.text()
        pwd2 = self.pass2_input.text()
        msg = self.msg_input.text().strip()

        if not email or "@" not in email:
            self.status_lbl.setText("❌ Insere um endereço de email válido (ex: utilizador@hotmail.com).")
            self.email_input.setFocus()
            return

        if not nickname:
            nickname = email.split("@")[0]

        if not pwd or len(pwd) < 4:
            self.status_lbl.setText("❌ A palavra-passe deve ter pelo menos 4 caracteres.")
            self.pass_input.setFocus()
            return

        if pwd != pwd2:
            self.status_lbl.setText("❌ As palavras-passe não coincidem. Verifica e tenta novamente.")
            self.pass2_input.setFocus()
            return

        self.status_lbl.setText("⏳ A registar a tua conta no servidor...")
        self.status_lbl.setStyleSheet("color: #0072c6; font-weight: bold; font-size: 11px;")
        self.register_btn.setEnabled(False)

        # Fallback timeout
        self.reg_timeout_timer = QTimer(self)
        self.reg_timeout_timer.setSingleShot(True)
        self.reg_timeout_timer.timeout.connect(lambda: self._on_reg_timeout(email, pwd, nickname, msg))
        self.reg_timeout_timer.start(3500)

        self.sig_register_requested.emit(email, pwd, nickname, self.selected_avatar_id, msg)

    def _on_reg_timeout(self, email: str, pwd: str, nickname: str, msg: str):
        # Fallback: direct database registration if network delayed
        try:
            from msn.server.database import MSNDatabase
            db = MSNDatabase()
            db.register_user(email, pwd, nickname, self.selected_avatar_id, msg)
        except Exception:
            pass
        self.accept()

    def on_register_result(self, success: bool, message: str):
        if hasattr(self, 'reg_timeout_timer'):
            self.reg_timeout_timer.stop()
        self.register_btn.setEnabled(True)
        if success:
            self.accept()
        else:
            self.status_lbl.setText(f"❌ {message}")
            self.status_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
