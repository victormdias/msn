"""
MSN Messenger Chat Window (Conversação)
Complete with Nudge (Chamar a Atenção / Screen Shake), Emoticons picker,
rich text formatting, typing indicator, sound effects, voice clips, and integrated mini-games.
"""
import base64
import os
import time
from typing import Optional
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QTextEdit,
    QPushButton, QFrame, QMenu, QColorDialog, QFileDialog, QScrollArea, QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QIcon, QKeyEvent, QMovie

from msn.common.protocol import UserProfile, UserStatus
from msn.client.emoticons import MSN_EMOTICONS, parse_emoticons_to_html, generate_avatar_pixmap, AVATAR_PRESETS
from msn.client.audio import MSNAudioManager
from msn.client.gui.game_dialog import MSNTicTacToeDialog
from msn.client.video_engine import VideoCaptureWorker, decode_b64_jpeg_to_pixmap


class EmoticonPickerPopup(QFrame):
    sig_emoticon_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("HeaderFrame")
        self.setFixedSize(260, 200)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        title = QLabel("<b>Emoticons do MSN</b>")
        title.setStyleSheet("font-size: 11px; color: #0072c6;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(4)

        shortcuts = list(MSN_EMOTICONS.keys())
        # Deduplicate representations
        seen_emojis = set()
        unique_shortcuts = []
        for s in shortcuts:
            emoji = MSN_EMOTICONS[s][0]
            if emoji not in seen_emojis:
                seen_emojis.add(emoji)
                unique_shortcuts.append(s)

        row, col = 0, 0
        for sc in unique_shortcuts:
            emoji, desc, _ = MSN_EMOTICONS[sc]
            btn = QPushButton(emoji)
            btn.setFixedSize(32, 32)
            btn.setToolTip(f"{desc} ({sc})")
            btn.setStyleSheet("font-size: 16px; padding: 0px;")
            btn.clicked.connect(lambda checked, s=sc: self._on_selected(s))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 6:
                col = 0
                row += 1

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _on_selected(self, shortcut: str):
        self.sig_emoticon_selected.emit(shortcut)
        self.close()


class MSNChatWindow(QWidget):
    sig_send_msg = pyqtSignal(str, str, str, str, bool, bool)  # target, text, color, font, bold, italic
    sig_send_nudge = pyqtSignal(str)                           # target
    sig_send_typing = pyqtSignal(str, bool)                    # target, is_typing
    sig_send_game_invite = pyqtSignal(str, str)                # target, game_type
    sig_send_voice_clip = pyqtSignal(str, bytes)               # target, wav_bytes
    sig_send_video_frame = pyqtSignal(str, str)                # target, b64_jpeg
    sig_send_video_toggle = pyqtSignal(str, bool)              # target, enabled

    def __init__(self, my_profile: UserProfile, contact_profile: UserProfile, parent=None):
        super().__init__(parent)
        self.my_profile = my_profile
        self.contact = contact_profile
        self.audio = MSNAudioManager.get_instance()

        self.text_color = "#1a4a6e"
        self.text_font = "Segoe UI"
        self.text_bold = False
        self.text_italic = False

        self.last_nudge_time = 0.0
        self.active_game_dialog: Optional[MSNTicTacToeDialog] = None
        self.video_worker: Optional[VideoCaptureWorker] = None
        self.is_video_active = False

        self.setWindowTitle(f"{self.contact.nickname} - Conversação")
        self.resize(580, 620)

        # Set window icon to logo.png
        possible_logo_paths = [
            os.path.abspath("logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logo.png"),
        ]
        logo_file = next((p for p in possible_logo_paths if os.path.exists(p)), None)
        if logo_file:
            self.setWindowIcon(QIcon(logo_file))

        self._init_ui()

        # Typing reset timer
        self.typing_clear_timer = QTimer(self)
        self.typing_clear_timer.setSingleShot(True)
        self.typing_clear_timer.timeout.connect(self._clear_typing_indicator)

        # Local typing debounce timer
        self.local_typing_timer = QTimer(self)
        self.local_typing_timer.setSingleShot(True)
        self.local_typing_timer.setInterval(2000)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Top Banner Header
        top_banner = QFrame()
        top_banner.setObjectName("ChatTopBanner")
        banner_layout = QHBoxLayout(top_banner)
        banner_layout.setContentsMargins(8, 6, 8, 6)
        banner_layout.setSpacing(10)

        # Contact Avatar
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.contact.avatar_id, size=48))
        self.avatar_lbl.setFixedSize(50, 50)
        banner_layout.addWidget(self.avatar_lbl)

        # Contact Info Layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.nick_lbl = QLabel(f"<b>{self.contact.nickname}</b> <span style='font-size: 11px; color: #555555;'>({self.contact.email})</span>")
        self.nick_lbl.setStyleSheet("font-size: 13px; color: #0b375b;")
        info_layout.addWidget(self.nick_lbl)

        self.status_msg_lbl = QLabel(self.contact.personal_msg or f"<{self.contact.status.label_pt}>")
        self.status_msg_lbl.setStyleSheet("font-size: 11px; color: #557a95; font-style: italic;")
        info_layout.addWidget(self.status_msg_lbl)

        banner_layout.addLayout(info_layout)
        banner_layout.addStretch()

        # Animated MSN Logo GIF in the top-right corner
        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(50, 50)
        self.logo_lbl.setScaledContents(True)

        possible_gif_paths = [
            os.path.abspath("logo.gif"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logo.gif"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logo.gif"),
        ]
        gif_file = next((p for p in possible_gif_paths if os.path.exists(p)), None)
        if gif_file:
            self.logo_movie = QMovie(gif_file)
            self.logo_lbl.setMovie(self.logo_movie)
            self.logo_movie.start()

        banner_layout.addWidget(self.logo_lbl)

        main_layout.addWidget(top_banner)

        # Toolbar for MSN Actions
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        # Nudge Button
        self.nudge_btn = QPushButton("⚡ Chamar a Atenção!")
        self.nudge_btn.setObjectName("NudgeBtn")
        self.nudge_btn.setToolTip("Envia um Zumbido / Nudge e faz o ecrã tremer!")
        self.nudge_btn.clicked.connect(self._on_send_nudge)
        toolbar.addWidget(self.nudge_btn)

        # Emoticons Button
        self.emoticon_btn = QPushButton("😊 Emoticons")
        self.emoticon_btn.clicked.connect(self._open_emoticon_picker)
        toolbar.addWidget(self.emoticon_btn)

        # Text Format (Color)
        self.color_btn = QPushButton("🎨 Cor")
        self.color_btn.clicked.connect(self._choose_color)
        toolbar.addWidget(self.color_btn)

        # Bold / Italic Toggles
        self.bold_btn = QPushButton("<b>B</b>")
        self.bold_btn.setFixedWidth(28)
        self.bold_btn.setCheckable(True)
        self.bold_btn.toggled.connect(self._toggle_bold)
        toolbar.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("<i>I</i>")
        self.italic_btn.setFixedWidth(28)
        self.italic_btn.setCheckable(True)
        self.italic_btn.toggled.connect(self._toggle_italic)
        toolbar.addWidget(self.italic_btn)

        # Mini-Games Button
        self.games_btn = QPushButton("🎮 Jogo do Galo")
        self.games_btn.clicked.connect(self._start_tic_tac_toe)
        toolbar.addWidget(self.games_btn)

        # Voice Clip Button
        self.voice_btn = QPushButton("🎤 Gravar Voz")
        self.voice_btn.setToolTip("Grava e envia um clip de áudio de 3 segundos")
        self.voice_btn.clicked.connect(self._send_voice_clip)
        toolbar.addWidget(self.voice_btn)

        # Send File Button
        self.file_btn = QPushButton("📁 Enviar Ficheiro")
        self.file_btn.clicked.connect(self._send_file)
        toolbar.addWidget(self.file_btn)

        # Webcam / Video Call Button
        self.video_btn = QPushButton("📹 Câmara")
        self.video_btn.setCheckable(True)
        self.video_btn.setToolTip("Ligar / Desligar câmara de vídeo (Webcam)")
        self.video_btn.toggled.connect(self._toggle_webcam)
        toolbar.addWidget(self.video_btn)

        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # Dual Video Panel (Collapsible)
        self.video_panel = QFrame()
        self.video_panel.setObjectName("HeaderFrame")
        video_layout = QHBoxLayout(self.video_panel)
        video_layout.setContentsMargins(6, 6, 6, 6)
        video_layout.setSpacing(10)

        # Local Webcam Box
        local_vbox = QVBoxLayout()
        local_vbox.setSpacing(2)
        local_lbl = QLabel("<b>A Minha Câmara</b>")
        local_lbl.setStyleSheet("font-size: 11px; color: #0072c6;")
        self.local_video_tile = QLabel()
        self.local_video_tile.setFixedSize(200, 150)
        self.local_video_tile.setStyleSheet("background: #111; border: 2px solid #00A859; border-radius: 6px;")
        self.local_video_tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        local_vbox.addWidget(local_lbl)
        local_vbox.addWidget(self.local_video_tile)
        video_layout.addLayout(local_vbox)

        # Remote Contact Webcam Box
        remote_vbox = QVBoxLayout()
        remote_vbox.setSpacing(2)
        self.remote_video_lbl = QLabel(f"<b>Câmara de {self.contact.nickname}</b>")
        self.remote_video_lbl.setStyleSheet("font-size: 11px; color: #d35400;")
        self.remote_video_tile = QLabel("A aguardar câmara...")
        self.remote_video_tile.setFixedSize(200, 150)
        self.remote_video_tile.setStyleSheet("background: #111; color: #888; border: 2px solid #a3c8e5; border-radius: 6px;")
        self.remote_video_tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remote_vbox.addWidget(self.remote_video_lbl)
        remote_vbox.addWidget(self.remote_video_tile)
        video_layout.addLayout(remote_vbox)

        self.video_panel.hide()
        main_layout.addWidget(self.video_panel)

        # Chat History Browser
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(True)
        self.history_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #9fc8e8;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(self.history_browser, stretch=4)

        # Typing Status Label
        self.typing_lbl = QLabel("")
        self.typing_lbl.setStyleSheet("font-size: 11px; color: #7f8c8d; font-style: italic; min-height: 14px;")
        main_layout.addWidget(self.typing_lbl)

        # Input Area Layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(65)
        self.input_edit.setPlaceholderText("Escreve aqui uma mensagem e prime Enter...")
        self.input_edit.textChanged.connect(self._on_text_changed)
        # Custom key handling for Enter vs Shift+Enter
        self.input_edit.installEventFilter(self)
        input_layout.addWidget(self.input_edit, stretch=1)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.setObjectName("PrimaryBtn")
        self.send_btn.setFixedSize(80, 65)
        self.send_btn.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_btn)

        main_layout.addLayout(input_layout)

        # Print initial session header in chat
        self.append_system_msg(f"Conversação iniciada com <b>{self.contact.nickname}</b> em {time.strftime('%H:%M')}.")

    def eventFilter(self, obj, event):
        if obj == self.input_edit and event.type() == event.Type.KeyPress:
            key_event: QKeyEvent = event
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False  # Allow newline with Shift+Enter
                else:
                    self._on_send_message()
                    return True
        return super().eventFilter(obj, event)

    def _on_text_changed(self):
        if not self.local_typing_timer.isActive():
            self.sig_send_typing.emit(self.contact.email, True)
            self.local_typing_timer.start()

    def _on_send_message(self):
        raw_text = self.input_edit.toPlainText().strip()
        if not raw_text:
            return

        self.input_edit.clear()

        # Render on my history
        self.append_message(
            sender_name=self.my_profile.nickname,
            text=raw_text,
            is_me=True,
            color=self.text_color,
            font_family=self.text_font,
            bold=self.text_bold,
            italic=self.text_italic
        )

        # Emit to network
        self.sig_send_msg.emit(
            self.contact.email,
            raw_text,
            self.text_color,
            self.text_font,
            self.text_bold,
            self.text_italic
        )

    def _on_send_nudge(self):
        now = time.time()
        if now - self.last_nudge_time < 4.0:
            self.append_system_msg("Atenção: Não podes enviar zumbidos com tanta frequência!")
            return

        self.last_nudge_time = now
        self.append_system_msg("⚡ <b>Você acabou de chamar a atenção!</b>")
        self.shake_window()
        self.audio.play_nudge()
        self.sig_send_nudge.emit(self.contact.email)

    def receive_nudge(self):
        self.append_system_msg(f"⚡ <b>{self.contact.nickname} acabou de chamar a sua atenção!</b>")
        self.shake_window()
        self.audio.play_nudge()

    def shake_window(self):
        """Vigorously shakes the chat window in classic MSN Messenger fashion."""
        orig_pos = self.pos()
        offsets = [
            (-12, 0), (12, -8), (-10, 10), (10, -10),
            (-8, 6), (8, -6), (-6, 4), (6, -4),
            (-3, 2), (3, -2), (0, 0)
        ]

        for i, (dx, dy) in enumerate(offsets):
            QTimer.singleShot(i * 35, lambda p=QPoint(orig_pos.x() + dx, orig_pos.y() + dy): self.move(p))

    def append_message(self, sender_name: str, text: str, is_me: bool, color: str = "#000000", font_family: str = "Segoe UI", bold: bool = False, italic: bool = False, timestamp: float = None):
        t_str = time.strftime("%H:%M", time.localtime(timestamp or time.time()))
        name_color = "#0072c6" if is_me else "#d35400"

        # Replace smileys with HTML emojis
        html_content = parse_emoticons_to_html(text)

        weight_style = "font-weight: bold;" if bold else ""
        font_style = "font-style: italic;" if italic else ""

        html = f"""
        <div style="margin-bottom: 6px;">
            <span style="color: {name_color}; font-weight: bold; font-size: 12px;">{sender_name}</span>
            <span style="color: #8fa0af; font-size: 10px;"> ({t_str}):</span><br>
            <span style="color: {color}; font-family: '{font_family}', sans-serif; font-size: 13px; {weight_style} {font_style} margin-left: 4px;">
                {html_content}
            </span>
        </div>
        """
        self.history_browser.append(html)
        if not is_me:
            self.audio.play_message()

    def append_system_msg(self, text: str):
        html = f"""
        <div style="margin: 6px 0; padding: 4px 8px; background: #fdf5e6; border-left: 3px solid #f39c12; color: #b9770e; font-size: 11px;">
            {text}
        </div>
        """
        self.history_browser.append(html)

    def set_remote_typing(self, is_typing: bool):
        if is_typing:
            self.typing_lbl.setText(f"✍️ {self.contact.nickname} está a escrever uma mensagem...")
            self.typing_clear_timer.start(4000)
        else:
            self._clear_typing_indicator()

    def _clear_typing_indicator(self):
        self.typing_lbl.setText("")

    def _open_emoticon_picker(self):
        picker = EmoticonPickerPopup(self)
        picker.sig_emoticon_selected.connect(self._insert_emoticon)
        pos = self.emoticon_btn.mapToGlobal(QPoint(0, -210))
        picker.move(pos)
        picker.show()

    def _insert_emoticon(self, shortcut: str):
        self.input_edit.insertPlainText(f" {shortcut} ")
        self.input_edit.setFocus()

    def _choose_color(self):
        c = QColorDialog.getColor(QColor(self.text_color), self, "Escolher Cor do Texto do MSN")
        if c.isValid():
            self.text_color = c.name()
            self.color_btn.setStyleSheet(f"color: {self.text_color}; font-weight: bold;")

    def _toggle_bold(self, checked: bool):
        self.text_bold = checked

    def _toggle_italic(self, checked: bool):
        self.text_italic = checked

    def _start_tic_tac_toe(self):
        session_id = f"{min(self.my_profile.email, self.contact.email)}_{max(self.my_profile.email, self.contact.email)}_tictactoe"
        self.active_game_dialog = MSNTicTacToeDialog(
            opponent_email=self.contact.email,
            opponent_nick=self.contact.nickname,
            session_id=session_id,
            is_my_turn=True,
            my_mark="X",
            parent=self
        )
        self.active_game_dialog.sig_make_move.connect(self._on_game_dialog_move)
        self.active_game_dialog.show()

        self.append_system_msg(f"🎮 Convidaste <b>{self.contact.nickname}</b> para uma partida de Jogo do Galo!")
        self.sig_send_game_invite.emit(self.contact.email, "tictactoe")

    def _on_game_dialog_move(self, target_email: str, cell_idx: int, mark: str):
        session_id = f"{min(self.my_profile.email, self.contact.email)}_{max(self.my_profile.email, self.contact.email)}_tictactoe"
        from msn.common.protocol import Packet, MsgAction
        pkt = Packet(
            action=MsgAction.GAME_MOVE,
            sender=self.my_profile.email,
            target=target_email,
            payload={"session_id": session_id, "cell_idx": cell_idx, "mark": mark}
        )
        # Forward through parent window network
        if hasattr(self.parent(), "network") and self.parent().network:
            self.parent().network.send_packet(pkt)

    def handle_game_move(self, payload: dict):
        if self.active_game_dialog:
            cell_idx = payload.get("cell_idx", -1)
            mark = payload.get("mark", "O")
            self.active_game_dialog.receive_remote_move(cell_idx, mark)

    def _send_voice_clip(self):
        self.append_system_msg("🎤 A gravar clip de áudio (3 segundos)... Fale para o microfone!")
        self.voice_btn.setEnabled(False)
        QTimer.singleShot(100, self._record_and_dispatch_voice)

    def _record_and_dispatch_voice(self):
        wav_bytes = self.audio.record_voice_clip(duration=3.0)
        self.voice_btn.setEnabled(True)
        if wav_bytes:
            self.append_system_msg("🎵 <b>Clip de áudio enviado!</b>")
            self.sig_send_voice_clip.emit(self.contact.email, wav_bytes)
        else:
            self.append_system_msg("❌ Não foi possível gravar o clip de áudio.")

    def receive_voice_clip(self, wav_bytes: bytes):
        self.append_system_msg(f"🎵 <b>{self.contact.nickname} enviou-lhe um clip de voz!</b>")
        self.audio.play_raw_wav(wav_bytes)

    def _send_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar ficheiro para enviar", "", "Todos os Ficheiros (*.*)")
        if filepath:
            fname = os.path.basename(filepath)
            size_kb = os.path.getsize(filepath) / 1024
            self.append_system_msg(f"📁 <b>Ficheiro enviado:</b> {fname} ({size_kb:.1f} KB)")
            # Send notification message
            self.sig_send_msg.emit(
                self.contact.email,
                f"📁 [Ficheiro Partilhado: {fname} ({size_kb:.1f} KB)]",
                "#2980b9",
                "Segoe UI",
                True,
                False
            )

    def update_contact_profile(self, updated_contact: UserProfile):
        self.contact = updated_contact
        self.nick_lbl.setText(f"<b>{self.contact.nickname}</b> <span style='font-size: 11px; color: #555555;'>({self.contact.email})</span>")
        self.status_msg_lbl.setText(self.contact.personal_msg or f"<{self.contact.status.label_pt}>")
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.contact.avatar_id, size=48))

    def _toggle_webcam(self, checked: bool):
        self.is_video_active = checked
        if checked:
            self.video_panel.show()
            self.append_system_msg("📹 <b>A sua câmara de vídeo foi ligada!</b>")
            my_preset = AVATAR_PRESETS.get(self.my_profile.avatar_id, AVATAR_PRESETS["avatar_1"])
            self.video_worker = VideoCaptureWorker(avatar_emoji=my_preset.get("emoji", "🦋"))
            self.video_worker.sig_frame_captured.connect(self._on_local_frame_captured)
            self.video_worker.start()
            self.sig_send_video_toggle.emit(self.contact.email, True)
        else:
            if self.video_worker:
                self.video_worker.stop()
                self.video_worker = None
            self.local_video_tile.clear()
            self.local_video_tile.setText("Câmara Desligada")
            self.sig_send_video_toggle.emit(self.contact.email, False)
            self.append_system_msg("📹 <b>A sua câmara de vídeo foi desligada.</b>")
            if self.remote_video_tile.text() == "A aguardar câmara...":
                self.video_panel.hide()

    def _on_local_frame_captured(self, pixmap, b64_jpeg):
        scaled = pixmap.scaled(self.local_video_tile.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.local_video_tile.setPixmap(scaled)
        self.sig_send_video_frame.emit(self.contact.email, b64_jpeg)

    def receive_video_frame(self, b64_frame: str):
        pixmap = decode_b64_jpeg_to_pixmap(b64_frame)
        if pixmap:
            self.video_panel.show()
            scaled = pixmap.scaled(self.remote_video_tile.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.remote_video_tile.setPixmap(scaled)

    def receive_video_toggle(self, enabled: bool):
        if enabled:
            self.video_panel.show()
            self.append_system_msg(f"📹 <b>{self.contact.nickname} ligou a câmara de vídeo!</b>")
        else:
            self.remote_video_tile.clear()
            self.remote_video_tile.setText("Câmara Desligada")
            self.append_system_msg(f"📹 <b>{self.contact.nickname} desligou a câmara de vídeo.</b>")
            if not self.is_video_active:
                self.video_panel.hide()

    def closeEvent(self, event):
        if hasattr(self, 'logo_movie') and self.logo_movie:
            self.logo_movie.stop()
        if self.video_worker:
            self.video_worker.stop()
            self.video_worker = None
        super().closeEvent(event)
