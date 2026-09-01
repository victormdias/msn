"""
MSN Messenger Add Contact Dialog
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton
)


class MSNAddContactDialog(QDialog):
    sig_add_contact = pyqtSignal(str, str)  # email, group

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar um Contacto - Windows Live Messenger")
        self.setFixedSize(360, 220)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header_lbl = QLabel("<b>Adicionar um novo amigo ao MSN</b>")
        header_lbl.setStyleSheet("color: #0072c6; font-size: 14px;")
        layout.addWidget(header_lbl)

        desc_lbl = QLabel("Insere o endereço de email do Windows Live / Hotmail da pessoa que desejas adicionar:")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #555555; font-size: 12px;")
        layout.addWidget(desc_lbl)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@hotmail.com")
        layout.addWidget(self.email_input)

        group_layout = QHBoxLayout()
        group_lbl = QLabel("Grupo:")
        self.group_combo = QComboBox()
        self.group_combo.addItems(["Amigos", "Favoritos", "Família", "Trabalho"])
        group_layout.addWidget(group_lbl)
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Adicionar")
        self.add_btn.setObjectName("PrimaryBtn")
        self.add_btn.clicked.connect(self._on_add)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

    def _on_add(self):
        email = self.email_input.text().strip().lower()
        if email and "@" in email:
            group = self.group_combo.currentText()
            self.sig_add_contact.emit(email, group)
            self.accept()
