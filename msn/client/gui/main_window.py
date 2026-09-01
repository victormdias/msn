"""
MSN Messenger Main Window (Buddy List / Lista de Contactos)
Complete with personal status header, search filter, categorized buddy groups,
right-click context menus, and active chat window manager.
"""
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRect, QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem, QMenu,
    QFrame, QMessageBox, QTabWidget, QSystemTrayIcon
)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QCursor, QAction, QColor, QBrush, QPen, QGuiApplication

from msn.common.protocol import UserProfile, UserStatus
from msn.client.emoticons import generate_avatar_pixmap, parse_emoticons_to_html
from msn.client.audio import MSNAudioManager
from msn.client.network import MSNNetworkClient
from msn.client.gui.chat_window import MSNChatWindow
from msn.client.gui.toast_notify import MSNToast
from msn.client.gui.add_contact import MSNAddContactDialog
from msn.client.gui.avatar_picker import MSNAvatarPickerDialog
from msn.client.gui.options_dialog import MSNOptionsDialog, load_app_settings


class MSNMainWindow(QMainWindow):
    def __init__(self, profile: UserProfile, contacts: List[UserProfile], network: MSNNetworkClient):
        super().__init__()
        self.profile = profile
        self.network = network
        self.audio = MSNAudioManager.get_instance()

        # Contacts storage: email -> UserProfile
        self.contacts_map: Dict[str, UserProfile] = {c.email: c for c in contacts}

        # Active chat windows: email -> MSNChatWindow
        self.active_chats: Dict[str, MSNChatWindow] = {}

        self.setWindowTitle(f"Windows Live Messenger - {self.profile.nickname}")
        self.resize(340, 680)
        self._init_ui()
        self._setup_network_signals()

        # Play welcome login chime
        self.audio.play_login()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 1. Profile Header Area
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(10)

        # Profile Avatar Box with Change Button
        avatar_vbox = QVBoxLayout()
        avatar_vbox.setSpacing(2)
        avatar_vbox.setContentsMargins(0, 0, 0, 0)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(self.profile.avatar_id, size=52))
        self.avatar_lbl.setFixedSize(54, 54)
        self.avatar_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.avatar_lbl.setToolTip("Clica para mudar a tua imagem de exibição ou carregar fotografia...")
        self.avatar_lbl.mousePressEvent = lambda e: self._open_avatar_picker_dialog()
        avatar_vbox.addWidget(self.avatar_lbl)

        self.change_avatar_btn = QPushButton("Mudar...")
        self.change_avatar_btn.setFixedHeight(18)
        self.change_avatar_btn.setFixedWidth(54)
        self.change_avatar_btn.setStyleSheet("font-size: 9px; padding: 1px 2px; color: #0072c6;")
        self.change_avatar_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.change_avatar_btn.clicked.connect(self._open_avatar_picker_dialog)
        avatar_vbox.addWidget(self.change_avatar_btn)

        header_layout.addLayout(avatar_vbox)

        # User Info Layout
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)

        # Display Nickname
        self.nick_edit = QLineEdit(self.profile.nickname)
        self.nick_edit.setStyleSheet("font-weight: bold; font-size: 13px; color: #0b375b; border: none; background: transparent;")
        self.nick_edit.setToolTip("Clica para alterar o teu Nickname")
        self.nick_edit.returnPressed.connect(self._on_profile_updated)
        user_info_layout.addWidget(self.nick_edit)

        # Personal Status Message ("O que está a ouvir?...")
        self.personal_msg_edit = QLineEdit(self.profile.personal_msg or "Partilhar uma mensagem pessoal...")
        self.personal_msg_edit.setStyleSheet("font-size: 11px; color: #557a95; border: 1px solid transparent; background: transparent; font-style: italic;")
        self.personal_msg_edit.setToolTip("Clica e prime Enter para atualizar a tua mensagem pessoal")
        self.personal_msg_edit.returnPressed.connect(self._on_profile_updated)
        user_info_layout.addWidget(self.personal_msg_edit)

        # Status Selector Combo
        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(140)
        for s in [UserStatus.ONLINE, UserStatus.BUSY, UserStatus.BRB, UserStatus.AWAY, UserStatus.INVISIBLE]:
            self.status_combo.addItem(f"{s.icon_char} {s.label_pt}", s)
        self.status_combo.currentIndexChanged.connect(self._on_status_combo_changed)
        user_info_layout.addWidget(self.status_combo)

        header_layout.addLayout(user_info_layout)
        main_layout.addWidget(header_frame)

        # 2. Search / Filter Box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Localizar um contacto...")
        self.search_input.textChanged.connect(self._filter_contacts)
        search_layout.addWidget(self.search_input)

        self.add_contact_btn = QPushButton("➕")
        self.add_contact_btn.setToolTip("Adicionar um novo contacto")
        self.add_contact_btn.setFixedSize(30, 28)
        self.add_contact_btn.clicked.connect(self._open_add_contact_dialog)
        search_layout.addWidget(self.add_contact_btn)

        main_layout.addLayout(search_layout)

        # 3. Contact Tree Widget (Buddy List)
        self.contact_tree = QTreeWidget()
        self.contact_tree.setHeaderHidden(True)
        self.contact_tree.setIndentation(16)
        self.contact_tree.setIconSize(QSize(28, 28))
        self.contact_tree.itemDoubleClicked.connect(self._on_contact_double_clicked)
        self.contact_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contact_tree.customContextMenuRequested.connect(self._show_contact_context_menu)
        main_layout.addWidget(self.contact_tree, stretch=1)

        # 4. Bottom Footer Toolbar
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(4, 2, 4, 2)

        self.mail_btn = QPushButton("✉️ Caixa de Entrada (0)")
        self.mail_btn.setStyleSheet("font-size: 11px;")
        footer_layout.addWidget(self.mail_btn)

        footer_layout.addStretch()

        icon_btn_style = """
            QPushButton {
                font-family: 'Segoe UI Emoji', 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 0px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.5 #e2f1fc, stop:0.51 #cde5f7, stop:1 #badbf3);
                border: 1px solid #7eaed3;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.5 #eef7fe, stop:0.51 #dbeffe, stop:1 #cbe7fc);
                border: 1px solid #0072c6;
            }
        """
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(34, 28)
        self.mute_btn.setStyleSheet(icon_btn_style)
        self.mute_btn.setToolTip("Silenciar / Ativar sons do MSN")
        self.mute_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mute_btn.clicked.connect(self._toggle_mute)
        footer_layout.addWidget(self.mute_btn)

        self.options_btn = QPushButton("⚙️")
        self.options_btn.setFixedSize(34, 28)
        self.options_btn.setStyleSheet(icon_btn_style)
        self.options_btn.setToolTip("Opções e Definições do MSN...")
        self.options_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.options_btn.clicked.connect(self._open_options_dialog)
        footer_layout.addWidget(self.options_btn)

        main_layout.addLayout(footer_layout)

        # Setup MSN Icon right at the Windows clock area
        self._setup_tray_icon()

        # Populate contacts in Tree
        self.refresh_contact_tree()

    def _setup_network_signals(self):
        self.network.sig_contact_status_changed.connect(self.on_contact_status_changed)
        self.network.sig_message_received.connect(self.on_message_received)
        self.network.sig_typing_received.connect(self.on_typing_received)
        self.network.sig_nudge_received.connect(self.on_nudge_received)
        self.network.sig_game_invite.connect(self.on_game_invite)
        self.network.sig_game_move.connect(self.on_game_move)
        self.network.sig_voice_clip_received.connect(self.on_voice_clip_received)
        self.network.sig_video_frame_received.connect(self.on_video_frame_received)
        self.network.sig_video_toggle_received.connect(self.on_video_toggle_received)
        self.network.sig_contact_added.connect(self.on_contact_added)

    def refresh_contact_tree(self, filter_text: str = ""):
        self.contact_tree.clear()
        filter_text = filter_text.strip().lower()

        # Categorize contacts
        favorites: List[UserProfile] = []
        online: List[UserProfile] = []
        busy_away: List[UserProfile] = []
        offline: List[UserProfile] = []

        for c in self.contacts_map.values():
            if filter_text and filter_text not in c.nickname.lower() and filter_text not in c.email.lower():
                continue

            if c.group == "Favoritos":
                favorites.append(c)
            elif c.status == UserStatus.ONLINE:
                online.append(c)
            elif c.status in (UserStatus.BUSY, UserStatus.AWAY, UserStatus.BRB, UserStatus.PHONE, UserStatus.LUNCH):
                busy_away.append(c)
            else:
                offline.append(c)

        # Add Favorite group
        if favorites:
            self._add_group_node("🌟 Favoritos", favorites, expanded=True)

        # Add Online group
        self._add_group_node(f"🟢 Disponível ({len(online)})", online, expanded=True)

        # Add Away / Busy group
        if busy_away:
            self._add_group_node(f"🔴 Ocupado / Ausente ({len(busy_away)})", busy_away, expanded=True)

        # Add Offline group
        self._add_group_node(f"⚪ Desligado ({len(offline)})", offline, expanded=False)

    def _add_group_node(self, header_title: str, contacts: List[UserProfile], expanded: bool = True):
        group_item = QTreeWidgetItem([header_title])
        group_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        group_item.setForeground(0, QColor("#1a4a6e"))
        self.contact_tree.addTopLevelItem(group_item)

        for c in contacts:
            item = QTreeWidgetItem()
            display_text = f"{c.status.icon_char}  {c.nickname}"
            if c.personal_msg:
                display_text += f"\n   ↳ <i>{c.personal_msg}</i>"

            item.setText(0, f"{c.status.icon_char}  {c.nickname}  ({c.personal_msg or c.status.label_pt})")
            item.setIcon(0, QIcon(generate_avatar_pixmap(c.avatar_id, size=24)))
            item.setData(0, Qt.ItemDataRole.UserRole, c.email)

            if c.status == UserStatus.OFFLINE:
                item.setForeground(0, QColor("#8fa0af"))
            else:
                item.setForeground(0, QColor("#1a252f"))

            group_item.addChild(item)

        group_item.setExpanded(expanded)

    def _filter_contacts(self, text: str):
        self.refresh_contact_tree(text)

    def _on_contact_double_clicked(self, item: QTreeWidgetItem, column: int):
        email = item.data(0, Qt.ItemDataRole.UserRole)
        if email and email in self.contacts_map:
            self.open_chat_window(self.contacts_map[email])

    def open_chat_window(self, contact: UserProfile) -> MSNChatWindow:
        if contact.email in self.active_chats:
            chat = self.active_chats[contact.email]
            chat.show()
            chat.raise_()
            chat.activateWindow()
            return chat

        chat = MSNChatWindow(self.profile, contact)
        chat.sig_send_msg.connect(self._on_chat_send_msg)
        chat.sig_send_nudge.connect(self._on_chat_send_nudge)
        chat.sig_send_typing.connect(self._on_chat_send_typing)
        chat.sig_send_game_invite.connect(self._on_chat_send_game_invite)
        chat.sig_send_voice_clip.connect(self._on_chat_send_voice_clip)
        chat.sig_send_video_frame.connect(self._on_chat_send_video_frame)
        chat.sig_send_video_toggle.connect(self._on_chat_send_video_toggle)

        self.active_chats[contact.email] = chat
        chat.show()
        return chat

    def _on_chat_send_msg(self, target: str, text: str, color: str, font: str, bold: bool, italic: bool):
        self.network.send_message(target, text, color, font, bold, italic)

    def _on_chat_send_nudge(self, target: str):
        self.network.send_nudge(target)

    def _on_chat_send_typing(self, target: str, is_typing: bool):
        self.network.send_typing(target, is_typing)

    def _on_chat_send_game_invite(self, target: str, game_type: str):
        self.network.send_game_invite(target, game_type)

    def _on_chat_send_voice_clip(self, target: str, wav_bytes: bytes):
        self.network.send_voice_clip(target, wav_bytes)

    def _on_chat_send_video_frame(self, target: str, b64_frame: str):
        self.network.send_video_frame(target, b64_frame)

    def _on_chat_send_video_toggle(self, target: str, enabled: bool):
        self.network.send_video_toggle(target, enabled)

    def _open_avatar_picker_dialog(self):
        dlg = MSNAvatarPickerDialog(self.profile.avatar_id, self)
        dlg.sig_avatar_chosen.connect(self._on_avatar_chosen)
        dlg.exec()

    def _on_avatar_chosen(self, new_avatar_id: str):
        self.profile.avatar_id = new_avatar_id
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(new_avatar_id, size=52))
        self.network.update_presence(self.profile.status, avatar_id=new_avatar_id)

        # Save to local preferences so login screen also loads it next time
        try:
            settings = load_app_settings()
            settings["avatar_id"] = new_avatar_id
            from msn.client.gui.options_dialog import save_app_settings
            save_app_settings(settings)
        except Exception:
            pass

        # Update any active open chat windows
        for chat in self.active_chats.values():
            chat.my_profile.avatar_id = new_avatar_id

    def _on_profile_updated(self):
        nick = self.nick_edit.text().strip() or self.profile.nickname
        msg = self.personal_msg_edit.text().strip()
        self.profile.nickname = nick
        self.profile.personal_msg = msg
        self.network.update_presence(self.profile.status, personal_msg=msg, nickname=nick, avatar_id=self.profile.avatar_id)

    def _on_status_combo_changed(self, idx: int):
        new_status = self.status_combo.currentData()
        if new_status:
            self.profile.status = new_status
            self.network.update_presence(new_status)

    def _open_options_dialog(self):
        dlg = MSNOptionsDialog(self)
        dlg.sig_settings_updated.connect(self._on_settings_updated)
        dlg.exec()

    def _on_settings_updated(self, settings: dict):
        self.audio.muted = not settings.get("enable_sounds", True)
        self.mute_btn.setText("🔇" if self.audio.muted else "🔊")

    def _setup_tray_icon(self):
        import os
        possible_logo_paths = [
            os.path.abspath("logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logo.png"),
        ]
        logo_file = next((p for p in possible_logo_paths if os.path.exists(p)), None)
        app_icon = QIcon(logo_file) if logo_file else QIcon(generate_avatar_pixmap(self.profile.avatar_id, size=32))

        self.setWindowIcon(app_icon)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip(f"Windows Live Messenger - {self.profile.nickname}")

        tray_menu = QMenu()
        open_action = tray_menu.addAction("🦋 Abrir Windows Live Messenger")
        open_action.triggered.connect(self.show_slide_up_from_tray)

        options_action = tray_menu.addAction("⚙️ Opções e Definições...")
        options_action.triggered.connect(self._open_options_dialog)

        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("🚪 Fechar Sessão / Sair")
        quit_action.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.show_slide_up_from_tray()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                # When minimized, hide from Windows Taskbar so it only stays at the clock!
                QTimer.singleShot(0, self.hide)
        super().changeEvent(event)

    def closeEvent(self, event):
        # When user closes window, hide to clock area instead of terminating app
        event.ignore()
        self.hide()

    def _quit_application(self):
        from PyQt6.QtWidgets import QApplication
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def show_slide_up_from_tray(self):
        # Animates the main window sliding up smoothly from the bottom right corner (Windows clock)
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.show()
            return

        screen_geo = screen.availableGeometry()
        w = 340
        h = min(680, screen_geo.height() - 30)

        end_x = screen_geo.right() - w - 10
        end_y = screen_geo.bottom() - h - 4

        start_x = end_x
        start_y = screen_geo.bottom() + 10

        self.setGeometry(start_x, start_y, w, h)
        self.show()
        self.raise_()
        self.activateWindow()

        self.slide_anim = QPropertyAnimation(self, b"geometry")
        self.slide_anim.setDuration(420)
        self.slide_anim.setStartValue(QRect(start_x, start_y, w, h))
        self.slide_anim.setEndValue(QRect(end_x, end_y, w, h))
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_anim.start()

    def _open_add_contact_dialog(self):
        dlg = MSNAddContactDialog(self)
        dlg.sig_add_contact.connect(self._on_add_contact_submitted)
        dlg.exec()

    def _on_add_contact_submitted(self, email: str, group: str):
        self.network.add_contact(email)

    def _toggle_mute(self):
        self.audio.muted = not self.audio.muted
        self.mute_btn.setText("🔇" if self.audio.muted else "🔊")

    # ---- Incoming Network Events ----

    def on_contact_status_changed(self, contact_dict: dict):
        c_prof = UserProfile.from_dict(contact_dict)
        prev_status = self.contacts_map[c_prof.email].status if c_prof.email in self.contacts_map else UserStatus.OFFLINE
        self.contacts_map[c_prof.email] = c_prof
        self.refresh_contact_tree(self.search_input.text())

        # Update open chat if any
        if c_prof.email in self.active_chats:
            self.active_chats[c_prof.email].update_contact_profile(c_prof)

        # If contact just came online, play chime and show MSN Toast popup!
        if prev_status == UserStatus.OFFLINE and c_prof.status != UserStatus.OFFLINE:
            self.audio.play_online()
            toast = MSNToast(
                contact_email=c_prof.email,
                title=c_prof.nickname,
                message="acabou de iniciar sessão.",
                avatar_id=c_prof.avatar_id
            )
            toast.clicked.connect(lambda email: self.open_chat_window(self.contacts_map[email]))
            toast.show_toast()

    def on_message_received(self, sender: str, payload: dict, timestamp: float):
        contact = self.contacts_map.get(sender, UserProfile(email=sender, nickname=sender.split("@")[0]))
        chat = self.open_chat_window(contact)
        chat.append_message(
            sender_name=contact.nickname,
            text=payload.get("text", ""),
            is_me=False,
            color=payload.get("color", "#000000"),
            font_family=payload.get("font", "Segoe UI"),
            bold=payload.get("bold", False),
            italic=payload.get("italic", False),
            timestamp=timestamp
        )

    def on_typing_received(self, sender: str, is_typing: bool):
        if sender in self.active_chats:
            self.active_chats[sender].set_remote_typing(is_typing)

    def on_nudge_received(self, sender: str):
        contact = self.contacts_map.get(sender, UserProfile(email=sender, nickname=sender.split("@")[0]))
        chat = self.open_chat_window(contact)
        chat.receive_nudge()

    def on_game_invite(self, sender: str, payload: dict):
        contact = self.contacts_map.get(sender, UserProfile(email=sender, nickname=sender.split("@")[0]))
        chat = self.open_chat_window(contact)
        chat.append_system_msg(f"🎮 <b>{contact.nickname}</b> convidou-te para um Jogo do Galo!")

    def on_game_move(self, sender: str, payload: dict):
        if sender in self.active_chats:
            self.active_chats[sender].handle_game_move(payload)

    def on_voice_clip_received(self, sender: str, wav_bytes: bytes):
        contact = self.contacts_map.get(sender, UserProfile(email=sender, nickname=sender.split("@")[0]))
        chat = self.open_chat_window(contact)
        chat.receive_voice_clip(wav_bytes)

    def on_video_frame_received(self, sender: str, b64_frame: str):
        if sender in self.active_chats:
            self.active_chats[sender].receive_video_frame(b64_frame)

    def on_video_toggle_received(self, sender: str, enabled: bool):
        contact = self.contacts_map.get(sender, UserProfile(email=sender, nickname=sender.split("@")[0]))
        chat = self.open_chat_window(contact)
        chat.receive_video_toggle(enabled)

    def on_contact_added(self, success: bool, contact_dict: dict):
        if success and contact_dict:
            c = UserProfile.from_dict(contact_dict)
            self.contacts_map[c.email] = c
            self.refresh_contact_tree(self.search_input.text())
            QMessageBox.information(self, "Contacto Adicionado", f"O contacto {c.nickname} ({c.email}) foi adicionado com sucesso!")

    def _show_contact_context_menu(self, pos):
        item = self.contact_tree.itemAt(pos)
        if not item or not item.parent():
            return  # Clicked on category header

        email = item.data(0, Qt.ItemDataRole.UserRole)
        if not email or email not in self.contacts_map:
            return

        contact = self.contacts_map[email]
        menu = QMenu(self)

        act_chat = menu.addAction("💬 Enviar uma Mensagem Instantânea")
        act_nudge = menu.addAction("⚡ Chamar a Atenção (Nudge)")
        menu.addSeparator()
        act_fav = menu.addAction("⭐ Mover para Favoritos")
        act_remove = menu.addAction("🗑️ Remover Contacto")

        chosen = menu.exec(self.contact_tree.mapToGlobal(pos))
        if chosen == act_chat:
            self.open_chat_window(contact)
        elif chosen == act_nudge:
            chat = self.open_chat_window(contact)
            chat._on_send_nudge()
        elif chosen == act_fav:
            contact.group = "Favoritos"
            self.refresh_contact_tree(self.search_input.text())
        elif chosen == act_remove:
            if email in self.contacts_map:
                del self.contacts_map[email]
                self.refresh_contact_tree(self.search_input.text())
