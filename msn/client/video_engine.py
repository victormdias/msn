"""
MSN Messenger Video Engine
Webcam capture, JPEG compression, base64 encoding, and QPixmap rendering.
Supports physical camera capture via OpenCV and automatic virtual animated avatar fallback.
"""
import base64
import math
import time
from typing import Optional
import cv2
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPen, QBrush


class VideoCaptureWorker(QThread):
    sig_frame_captured = pyqtSignal(QPixmap, str)  # local_pixmap, base64_jpeg

    def __init__(self, camera_index: int = 0, width: int = 320, height: int = 240, fps: int = 15, avatar_emoji: str = "🦋"):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.avatar_emoji = avatar_emoji
        self._running = False
        self.cap: Optional[cv2.VideoCapture] = None

    def run(self):
        self._running = True
        has_camera = False

        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                # Test reading one frame
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    has_camera = True
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                else:
                    self.cap.release()
                    self.cap = None
        except Exception:
            has_camera = False

        frame_interval = 1.0 / self.fps
        tick = 0

        while self._running:
            start_time = time.time()

            if has_camera and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Flip horizontally for natural mirror effect
                    frame = cv2.flip(frame, 1)
                    frame = cv2.resize(frame, (self.width, self.height))

                    # Convert to RGB for Qt
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img)

                    # Encode to compressed JPEG for network transmission
                    _, jpeg_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                    b64_str = base64.b64encode(jpeg_buf).decode('utf-8')

                    self.sig_frame_captured.emit(pixmap, b64_str)
            else:
                # Virtual Animated Camera Fallback
                pixmap, b64_str = self._generate_virtual_frame(tick)
                self.sig_frame_captured.emit(pixmap, b64_str)
                tick += 1

            elapsed = time.time() - start_time
            sleep_time = max(0.01, frame_interval - elapsed)
            time.sleep(sleep_time)

        if self.cap:
            self.cap.release()

    def _generate_virtual_frame(self, tick: int) -> tuple[QPixmap, str]:
        """Generates a pleasant animated avatar stream when no physical camera is present."""
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(QColor("#1b2838"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw glowing background pulse
        pulse = (math.sin(tick * 0.15) + 1.0) * 0.5
        bg_radius = int(60 + pulse * 20)
        center_x = self.width // 2
        center_y = self.height // 2 - 15

        painter.setPen(Qt.PenStyle.NoPen)
        glow_color = QColor(0, 168, 89, int(40 + pulse * 40))
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(center_x - bg_radius, center_y - bg_radius, bg_radius * 2, bg_radius * 2)

        # Draw Emoji Avatar
        font = QFont("Segoe UI Emoji", 48)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, 0, self.width, self.height - 30, Qt.AlignmentFlag.AlignCenter, self.avatar_emoji)

        # Draw Status Bar at bottom
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#00ff88"))
        painter.drawText(0, self.height - 24, self.width, 20, Qt.AlignmentFlag.AlignCenter, "● Câmara Virtual do MSN")

        painter.end()

        # Convert to Base64 JPEG
        q_img = pixmap.toImage()
        buffer = q_img.bits().asstring(q_img.sizeInBytes())
        arr = np.frombuffer(buffer, dtype=np.uint8).reshape((self.height, self.width, 4))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        _, jpeg_buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, 50])
        b64_str = base64.b64encode(jpeg_buf).decode('utf-8')

        return pixmap, b64_str

    def stop(self):
        self._running = False
        self.wait(1000)


def decode_b64_jpeg_to_pixmap(b64_str: str) -> Optional[QPixmap]:
    """Decodes incoming base64 JPEG from peer into a QPixmap."""
    try:
        raw_bytes = base64.b64decode(b64_str)
        nparr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            return QPixmap.fromImage(q_img)
    except Exception:
        pass
    return None
