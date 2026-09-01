"""
MSN Toast Notification Widget
Sliding notification popup in bottom-right corner of the desktop, just like Windows Live Messenger.
"""
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt6.QtGui import QPixmap, QCursor
from msn.client.emoticons import generate_avatar_pixmap


class MSNToast(QWidget):
    clicked = pyqtSignal(str)  # Emits contact email when clicked

    def __init__(self, contact_email: str, title: str, message: str, avatar_id: str = "avatar_1", duration_ms: int = 4000):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setObjectName("ToastWidget")
        self.contact_email = contact_email
        self.duration_ms = duration_ms
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.setFixedSize(280, 75)
        self._init_ui(title, message, avatar_id)
        self._setup_animation()

    def _init_ui(self, title: str, message: str, avatar_id: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Avatar
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setPixmap(generate_avatar_pixmap(avatar_id, size=46))
        self.avatar_lbl.setFixedSize(48, 48)
        layout.addWidget(self.avatar_lbl)

        # Text Layout
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # MSN Title
        self.header_lbl = QLabel("<b>Windows Live Messenger</b>")
        self.header_lbl.setStyleSheet("color: #0072c6; font-size: 11px; font-weight: bold;")
        text_layout.addWidget(self.header_lbl)

        # Contact Name
        self.title_lbl = QLabel(f"<b>{title}</b>")
        self.title_lbl.setStyleSheet("color: #1a4a6e; font-size: 12px;")
        self.title_lbl.setWordWrap(True)
        text_layout.addWidget(self.title_lbl)

        # Message / Status
        self.msg_lbl = QLabel(message)
        self.msg_lbl.setStyleSheet("color: #555555; font-size: 11px;")
        self.msg_lbl.setWordWrap(True)
        text_layout.addWidget(self.msg_lbl)

        layout.addLayout(text_layout)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _setup_animation(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.end_x = screen.width() - self.width() - 20
        self.end_y = screen.height() - self.height() - 10
        self.start_y = screen.height() + 10

        self.move(self.end_x, self.start_y)

        # Slide Up Animation
        self.anim_in = QPropertyAnimation(self, b"pos")
        self.anim_in.setDuration(450)
        self.anim_in.setStartValue(QPoint(self.end_x, self.start_y))
        self.anim_in.setEndValue(QPoint(self.end_x, self.end_y))
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide Down Animation
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(QPoint(self.end_x, self.end_y))
        self.anim_out.setEndValue(QPoint(self.end_x, self.start_y))
        self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim_out.finished.connect(self.close)

        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.slide_out)

    def show_toast(self):
        self.show()
        self.anim_in.start()
        self.dismiss_timer.start(self.duration_ms)

    def slide_out(self):
        self.anim_out.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.contact_email)
            self.close()
