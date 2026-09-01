"""
MSN Messenger Options / Preferences Dialog (Opções do Windows Live Messenger)
Comprehensive settings modal for:
- Sign-in credentials persistence (remember email, remember password, auto-login)
- Window behavior (slide-up from clock, minimize to tray)
- Sounds and notifications (sound effects, toast popups, nudge shake)
- Message styling (default font, color, emoticons)
- Server network connection endpoint
"""
import os
import json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QFrame, QWidget, QTabWidget, QColorDialog,
    QFontComboBox, QSpinBox, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon

from msn.client.audio import MSNAudioManager


CONFIG_FILE = "msn_settings.json"


def load_app_settings() -> dict:
    """Loads application settings with sensible MSN defaults."""
    defaults = {
        "remember_email": True,
        "saved_email": "",
        "remember_password": False,
        "saved_password": "",
        "auto_login": False,
        "slide_up_clock": True,
        "minimize_to_tray": True,
        "enable_sounds": True,
        "enable_toasts": True,
        "allow_nudges": True,
        "default_font": "Segoe UI",
        "default_color": "#1a4a6e",
        "show_emoticons": True,
        "send_typing": True,
        "server_address": "127.0.0.1:8800"
    }

    prefs_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE),
        CONFIG_FILE,
        "login_prefs.json"
    ]
    
    for p in prefs_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
                    break
            except Exception:
                pass

    return defaults


def save_app_settings(settings: dict):
    """Saves application settings to json file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


class MSNOptionsDialog(QDialog):
    sig_settings_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opções - Windows Live Messenger")
        self.setFixedSize(500, 540)
        self.settings = load_app_settings()
        self.audio = MSNAudioManager.get_instance()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Title Header
        title_frame = QFrame()
        title_frame.setObjectName("HeaderFrame")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 8, 10, 8)

        icon_lbl = QLabel("⚙️")
        icon_lbl.setStyleSheet("font-size: 22px;")
        title_layout.addWidget(icon_lbl)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        h_title = QLabel("<b>Definições e Opções do MSN Messenger</b>")
        h_title.setStyleSheet("font-size: 13px; color: #0072c6;")
        h_sub = QLabel("Personaliza o início de sessão, sons, notificações e ligação.")
        h_sub.setStyleSheet("font-size: 11px; color: #557a95;")
        header_text_layout.addWidget(h_title)
        header_text_layout.addWidget(h_sub)
        title_layout.addLayout(header_text_layout)
        title_layout.addStretch()

        main_layout.addWidget(title_frame)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #a3c8e5;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #eef6fb;
                border: 1px solid #a3c8e5;
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                color: #2c3e50;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                color: #0072c6;
            }
        """)

        # Tab 1: Início de Sessão & Geral
        tab_login = self._create_login_tab()
        self.tabs.addTab(tab_login, "👤 Início de Sessão")

        # Tab 2: Sons & Alertas
        tab_alerts = self._create_alerts_tab()
        self.tabs.addTab(tab_alerts, "🔔 Sons e Alertas")

        # Tab 3: Mensagens & Aspeto
        tab_messages = self._create_messages_tab()
        self.tabs.addTab(tab_messages, "💬 Mensagens")

        # Tab 4: Ligação / Servidor
        tab_connection = self._create_connection_tab()
        self.tabs.addTab(tab_connection, "🌐 Ligação")

        main_layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Guardar Definições")
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.setFixedHeight(34)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self._on_save_clicked)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _create_login_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp_cred = QGroupBox("Credenciais e Início Automático")
        grp_cred.setStyleSheet("font-weight: bold; color: #0b375b;")
        cred_layout = QVBoxLayout(grp_cred)
        cred_layout.setSpacing(8)

        self.cb_remember_email = QCheckBox("Guardar o meu endereço de email no ecrã de início")
        self.cb_remember_email.setChecked(self.settings.get("remember_email", True))
        self.cb_remember_email.setStyleSheet("font-weight: normal; color: #2c3e50;")
        cred_layout.addWidget(self.cb_remember_email)

        self.cb_remember_pass = QCheckBox("Guardar a minha palavra-passe (Não preencher se desmarcado)")
        self.cb_remember_pass.setChecked(self.settings.get("remember_password", False))
        self.cb_remember_pass.setStyleSheet("font-weight: normal; color: #2c3e50;")
        cred_layout.addWidget(self.cb_remember_pass)

        self.cb_auto_login = QCheckBox("Iniciar sessão automaticamente ao abrir o MSN")
        self.cb_auto_login.setChecked(self.settings.get("auto_login", False))
        self.cb_auto_login.setStyleSheet("font-weight: normal; color: #2c3e50;")
        cred_layout.addWidget(self.cb_auto_login)

        layout.addWidget(grp_cred)

        grp_window = QGroupBox("Comportamento da Janela")
        grp_window.setStyleSheet("font-weight: bold; color: #0b375b;")
        win_layout = QVBoxLayout(grp_window)
        win_layout.setSpacing(8)

        self.cb_slide_clock = QCheckBox("Fazer a janela de amigos subir junto ao relógio do Windows")
        self.cb_slide_clock.setChecked(self.settings.get("slide_up_clock", True))
        self.cb_slide_clock.setStyleSheet("font-weight: normal; color: #2c3e50;")
        win_layout.addWidget(self.cb_slide_clock)

        layout.addWidget(grp_window)
        layout.addStretch()
        return w

    def _create_alerts_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp_sound = QGroupBox("Sons do MSN")
        grp_sound.setStyleSheet("font-weight: bold; color: #0b375b;")
        sound_layout = QVBoxLayout(grp_sound)
        sound_layout.setSpacing(8)

        self.cb_sounds = QCheckBox("Ativar efeitos sonoros do MSN (Entrada, Mensagem, Zumbido)")
        self.cb_sounds.setChecked(self.settings.get("enable_sounds", True))
        self.cb_sounds.setStyleSheet("font-weight: normal; color: #2c3e50;")
        sound_layout.addWidget(self.cb_sounds)

        test_sound_btn = QPushButton("🔊 Testar Som de Entrada")
        test_sound_btn.setFixedWidth(160)
        test_sound_btn.clicked.connect(lambda: self.audio.play_login())
        sound_layout.addWidget(test_sound_btn)

        layout.addWidget(grp_sound)

        grp_notif = QGroupBox("Notificações de Amigos")
        grp_notif.setStyleSheet("font-weight: bold; color: #0b375b;")
        notif_layout = QVBoxLayout(grp_notif)
        notif_layout.setSpacing(8)

        self.cb_toasts = QCheckBox("Mostrar alertas no canto do ecrã quando um amigo entra ou escreve")
        self.cb_toasts.setChecked(self.settings.get("enable_toasts", True))
        self.cb_toasts.setStyleSheet("font-weight: normal; color: #2c3e50;")
        notif_layout.addWidget(self.cb_toasts)

        self.cb_nudges = QCheckBox("Permitir receber Zumbidos (Chamar a Atenção / Tremer ecrã)")
        self.cb_nudges.setChecked(self.settings.get("allow_nudges", True))
        self.cb_nudges.setStyleSheet("font-weight: normal; color: #2c3e50;")
        notif_layout.addWidget(self.cb_nudges)

        layout.addWidget(grp_notif)
        layout.addStretch()
        return w

    def _create_messages_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp_style = QGroupBox("Aspeto do Texto nas Conversas")
        grp_style.setStyleSheet("font-weight: bold; color: #0b375b;")
        style_layout = QVBoxLayout(grp_style)
        style_layout.setSpacing(8)

        font_row = QHBoxLayout()
        font_lbl = QLabel("Tipo de Letra:")
        font_lbl.setStyleSheet("font-weight: normal; color: #2c3e50;")
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.settings.get("default_font", "Segoe UI")))
        font_row.addWidget(font_lbl)
        font_row.addWidget(self.font_combo)
        style_layout.addLayout(font_row)

        color_row = QHBoxLayout()
        color_lbl = QLabel("Cor padrão do texto:")
        color_lbl.setStyleSheet("font-weight: normal; color: #2c3e50;")
        self.current_color = self.settings.get("default_color", "#1a4a6e")
        self.color_preview = QLabel("    Exemplo de Texto    ")
        self.color_preview.setStyleSheet(f"color: {self.current_color}; font-weight: bold; border: 1px solid #ccc; padding: 4px; background: white;")
        self.pick_color_btn = QPushButton("🎨 Escolher Cor...")
        self.pick_color_btn.clicked.connect(self._pick_text_color)
        color_row.addWidget(color_lbl)
        color_row.addWidget(self.color_preview)
        color_row.addWidget(self.pick_color_btn)
        style_layout.addLayout(color_row)

        layout.addWidget(grp_style)

        grp_misc = QGroupBox("Opções de Conversação")
        grp_misc.setStyleSheet("font-weight: bold; color: #0b375b;")
        misc_layout = QVBoxLayout(grp_misc)
        misc_layout.setSpacing(8)

        self.cb_emoticons = QCheckBox("Substituir atalhos como :) ou (L) por emoticons coloridos")
        self.cb_emoticons.setChecked(self.settings.get("show_emoticons", True))
        self.cb_emoticons.setStyleSheet("font-weight: normal; color: #2c3e50;")
        misc_layout.addWidget(self.cb_emoticons)

        self.cb_typing = QCheckBox("Enviar aviso de 'A escrever uma mensagem...' aos amigos")
        self.cb_typing.setChecked(self.settings.get("send_typing", True))
        self.cb_typing.setStyleSheet("font-weight: normal; color: #2c3e50;")
        misc_layout.addWidget(self.cb_typing)

        layout.addWidget(grp_misc)
        layout.addStretch()
        return w

    def _create_connection_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp_server = QGroupBox("Servidor Central do MSN")
        grp_server.setStyleSheet("font-weight: bold; color: #0b375b;")
        srv_layout = QVBoxLayout(grp_server)
        srv_layout.setSpacing(8)

        srv_desc = QLabel("Endereço do servidor ao qual o MSN se liga (ex: 127.0.0.1:8800 ou o teu servidor na Nuvem):")
        srv_desc.setStyleSheet("font-weight: normal; color: #557a95; font-size: 11px;")
        srv_desc.setWordWrap(True)
        srv_layout.addWidget(srv_desc)

        self.server_input = QLineEdit(self.settings.get("server_address", "127.0.0.1:8800"))
        self.server_input.setFixedHeight(32)
        self.server_input.setStyleSheet("font-weight: normal; font-size: 12px;")
        srv_layout.addWidget(self.server_input)

        layout.addWidget(grp_server)
        layout.addStretch()
        return w

    def _pick_text_color(self):
        col = QColorDialog.getColor(QColor(self.current_color), self, "Escolher Cor do Texto")
        if col.isValid():
            self.current_color = col.name()
            self.color_preview.setStyleSheet(f"color: {self.current_color}; font-weight: bold; border: 1px solid #ccc; padding: 4px; background: white;")

    def _on_save_clicked(self):
        updated = {
            "remember_email": self.cb_remember_email.isChecked(),
            "remember_password": self.cb_remember_pass.isChecked(),
            "auto_login": self.cb_auto_login.isChecked(),
            "slide_up_clock": self.cb_slide_clock.isChecked(),
            "enable_sounds": self.cb_sounds.isChecked(),
            "enable_toasts": self.cb_toasts.isChecked(),
            "allow_nudges": self.cb_nudges.isChecked(),
            "default_font": self.font_combo.currentFont().family(),
            "default_color": self.current_color,
            "show_emoticons": self.cb_emoticons.isChecked(),
            "send_typing": self.cb_typing.isChecked(),
            "server_address": self.server_input.text().strip() or "127.0.0.1:8800"
        }

        # If user disabled remember_password, clear saved password
        if not updated["remember_password"]:
            updated["saved_password"] = ""
        else:
            updated["saved_password"] = self.settings.get("saved_password", "")

        if not updated["remember_email"]:
            updated["saved_email"] = ""
        else:
            updated["saved_email"] = self.settings.get("saved_email", "")

        save_app_settings(updated)
        self.audio.muted = not updated["enable_sounds"]

        self.sig_settings_updated.emit(updated)
        self.accept()
