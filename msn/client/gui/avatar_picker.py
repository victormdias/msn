"""
MSN Messenger Display Picture Selector (Mudar Imagem de Exibição / Fotografia)
Allows selecting classic MSN preset avatars or uploading custom photographs from the user's computer.
"""
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QFileDialog, QScrollArea, QGridLayout, QMessageBox
)
from PyQt6.QtGui import QFont, QPixmap, QColor, QCursor, QIcon

from msn.client.emoticons import (
    AVATAR_PRESETS, generate_avatar_pixmap, encode_image_file_to_avatar_str
)


class MSNAvatarPickerDialog(QDialog):
    sig_avatar_chosen = pyqtSignal(str)  # avatar_id or 'custom:<b64>'

    def __init__(self, current_avatar_id: str = "avatar_1", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Imagem de Exibição - Windows Live Messenger")
        self.setFixedSize(480, 520)
        self.selected_avatar_id = current_avatar_id
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Title
        title_lbl = QLabel("<b>Escolher uma Imagem de Exibição</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #0072c6;")
        main_layout.addWidget(title_lbl)

        # Top Preview Box
        preview_frame = QFrame()
        preview_frame.setObjectName("HeaderFrame")
        preview_layout = QHBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(14)

        self.preview_lbl = QLabel()
        self.preview_lbl.setPixmap(generate_avatar_pixmap(self.selected_avatar_id, size=80))
        self.preview_lbl.setFixedSize(84, 84)
        self.preview_lbl.setStyleSheet("border: 2px solid #a3c8e5; border-radius: 12px; background: white;")
        preview_layout.addWidget(self.preview_lbl)

        preview_text_layout = QVBoxLayout()
        preview_text_layout.setSpacing(4)
        self.preview_name_lbl = QLabel("<b>Imagem Atual</b>")
        self.preview_name_lbl.setStyleSheet("font-size: 13px; color: #0b375b;")
        preview_sub_lbl = QLabel("A tua imagem de exibição é visível para todos os teus contactos no MSN.")
        preview_sub_lbl.setStyleSheet("font-size: 11px; color: #557a95;")
        preview_sub_lbl.setWordWrap(True)
        preview_text_layout.addWidget(self.preview_name_lbl)
        preview_text_layout.addWidget(preview_sub_lbl)
        preview_layout.addLayout(preview_text_layout)

        main_layout.addWidget(preview_frame)

        # Choose Custom Photo Button
        photo_btn_layout = QHBoxLayout()
        self.browse_photo_btn = QPushButton("📁 Procurar / Carregar Fotografia do PC...")
        self.browse_photo_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e0f0fa);
                border: 1.5px solid #0072c6;
                color: #0072c6;
                font-weight: bold;
                padding: 7px 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #eef7fe;
                color: #005a9e;
            }
        """)
        self.browse_photo_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.browse_photo_btn.clicked.connect(self._on_browse_photo_clicked)
        photo_btn_layout.addWidget(self.browse_photo_btn)
        main_layout.addLayout(photo_btn_layout)

        # Preset Avatars Grid
        presets_lbl = QLabel("<b>Ou escolhe um avatar clássico do MSN:</b>")
        presets_lbl.setStyleSheet("font-size: 12px; color: #2c3e50;")
        main_layout.addWidget(presets_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: white; border: 1px solid #a3c8e5; border-radius: 6px;")
        
        container = QWidget()
        container.setStyleSheet("background: white;")
        grid = QGridLayout(container)
        grid.setSpacing(8)
        grid.setContentsMargins(8, 8, 8, 8)

        row, col = 0, 0
        for avatar_id, info in AVATAR_PRESETS.items():
            btn = QPushButton()
            pix = generate_avatar_pixmap(avatar_id, size=48)
            btn.setIcon(QIcon(pix))
            btn.setIconSize(pix.size())
            btn.setFixedSize(54, 54)
            btn.setToolTip(info["name"])
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    border: 2px solid #0072c6;
                    background: #f0f7fe;
                }
            """)
            btn.clicked.connect(lambda checked, a_id=avatar_id, name=info['name']: self._select_preset(a_id, name))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 6:
                col = 0
                row += 1

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Guardar e Aplicar")
        self.apply_btn.setObjectName("PrimaryBtn")
        self.apply_btn.setFixedHeight(36)
        self.apply_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.apply_btn.clicked.connect(self._on_apply_clicked)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        main_layout.addLayout(btn_layout)

    def _select_preset(self, avatar_id: str, name: str):
        self.selected_avatar_id = avatar_id
        self.preview_lbl.setPixmap(generate_avatar_pixmap(avatar_id, size=80))
        self.preview_name_lbl.setText(f"<b>{name}</b>")

    def _on_browse_photo_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Fotografia para o MSN",
            "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if filepath:
            custom_avatar_str = encode_image_file_to_avatar_str(filepath, max_size=180)
            if custom_avatar_str:
                self.selected_avatar_id = custom_avatar_str
                self.preview_lbl.setPixmap(generate_avatar_pixmap(custom_avatar_str, size=80))
                self.preview_name_lbl.setText("<b>Fotografia Personalizada</b>")

    def _on_apply_clicked(self):
        self.sig_avatar_chosen.emit(self.selected_avatar_id)
        self.accept()
