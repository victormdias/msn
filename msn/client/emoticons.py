"""
MSN Messenger Emoticons and Avatars catalog
Supports classic shortcut substitution, emoticon palette picker, and built-in avatar icons.
"""
import re
from typing import Dict, List, Tuple
from PyQt6.QtGui import QColor, QPainter, QPixmap, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QRectF

# Classic MSN Emoticon Mapping: Shortcut -> (Emoji / Display, Description, Category)
MSN_EMOTICONS: Dict[str, Tuple[str, str, str]] = {
    # Smileys
    ":)": ("😊", "Sorriso", "faces"),
    ":-)": ("😊", "Sorriso", "faces"),
    ":D": ("😃", "Riso Aberto", "faces"),
    ":-D": ("😃", "Riso Aberto", "faces"),
    ";)": ("😉", "Piscadela", "faces"),
    ";-)": ("😉", "Piscadela", "faces"),
    ":P": ("😛", "Língua de Fora", "faces"),
    ":-P": ("😛", "Língua de Fora", "faces"),
    ":p": ("😛", "Língua de Fora", "faces"),
    ":-p": ("😛", "Língua de Fora", "faces"),
    ":O": ("😮", "Surpreso", "faces"),
    ":-O": ("😮", "Surpreso", "faces"),
    ":o": ("😮", "Surpreso", "faces"),
    ":-o": ("😮", "Surpreso", "faces"),
    ":(": ("🙁", "Triste", "faces"),
    ":-(": ("🙁", "Triste", "faces"),
    ":'(": ("😢", "A chorar", "faces"),
    ":@": ("😡", "Zangado", "faces"),
    ":-@": ("😡", "Zangado", "faces"),
    ":S": ("😖", "Confuso", "faces"),
    ":-S": ("😖", "Confuso", "faces"),
    ":$": ("😳", "Envergonhado", "faces"),
    ":-$": ("😳", "Envergonhado", "faces"),
    ":|": ("😐", "Sem Expressão", "faces"),
    ":-|": ("😐", "Sem Expressão", "faces"),
    ":#": ("🤐", "Boca Fechada", "faces"),
    "8-)": ("🤓", "Nerd de Óculos", "faces"),

    # Classic MSN Iconic Codes
    "(L)": ("❤️", "Coração Vermelho (Love)", "classic"),
    "(l)": ("❤️", "Coração Vermelho", "classic"),
    "(U)": ("💔", "Coração Partido", "classic"),
    "(u)": ("💔", "Coração Partido", "classic"),
    "(Y)": ("👍", "Polegar para Cima (Yes)", "classic"),
    "(y)": ("👍", "Polegar para Cima", "classic"),
    "(N)": ("👎", "Polegar para Baixo (No)", "classic"),
    "(n)": ("👎", "Polegar para Baixo", "classic"),
    "(H)": ("😎", "Estiloso com Óculos de Sol (Cool)", "classic"),
    "(h)": ("😎", "Estiloso", "classic"),
    "(6)": ("😈", "Diabinho", "classic"),
    "(A)": ("😇", "Anjinho", "classic"),
    "(a)": ("😇", "Anjinho", "classic"),
    "(K)": ("💋", "Beijo (Kiss)", "classic"),
    "(k)": ("💋", "Beijo", "classic"),
    "(B)": ("🍺", "Cerveja (Beer)", "objects"),
    "(b)": ("🍺", "Cerveja", "objects"),
    "(D)": ("🍸", "Bebida (Drink)", "objects"),
    "(d)": ("🍸", "Bebida", "objects"),
    "(X)": ("👧", "Rapariga (Girl)", "people"),
    "(x)": ("👧", "Rapariga", "people"),
    "(Z)": ("👦", "Rapaz (Boy)", "people"),
    "(z)": ("👦", "Rapaz", "people"),
    "(M)": ("✉️", "Email / Mensagem", "objects"),
    "(m)": ("✉️", "Email", "objects"),
    "(8)": ("🎵", "Música (Nota Musical)", "objects"),
    "(G)": ("🎁", "Prenda", "objects"),
    "(g)": ("🎁", "Prenda", "objects"),
    "(F)": ("🌹", "Rosa Vermelha", "objects"),
    "(f)": ("🌹", "Rosa", "objects"),
    "(W)": ("🥀", "Flor Murcha", "objects"),
    "(w)": ("🥀", "Flor Murcha", "objects"),
    "(P)": ("📷", "Câmara Fotográfica", "objects"),
    "(p)": ("📷", "Câmara", "objects"),
    "(~)": ("🎬", "Cinema", "objects"),
    "(O)": ("⏰", "Relógio", "objects"),
    "(o)": ("⏰", "Relógio", "objects"),
    "(I)": ("💡", "Ideia / Lâmpada", "objects"),
    "(i)": ("💡", "Ideia", "objects"),
    "(C)": ("☕", "Café Quente", "objects"),
    "(c)": ("☕", "Café", "objects"),
    "({)": ("🤗", "Abraço Esquerdo", "classic"),
    "(})": ("🤗", "Abraço Direito", "classic"),
    "(S)": ("🌙", "Lua / Boa Noite", "objects"),
    "(s)": ("🌙", "Lua", "objects"),
    "(E)": ("💌", "Carta de Amor", "objects"),
    "(e)": ("💌", "Carta de Amor", "objects"),
    "(T)": ("📞", "Telefone", "objects"),
    "(t)": ("📞", "Telefone", "objects"),
    "(MP)": ("📱", "Telemóvel", "objects"),
    "(mp)": ("📱", "Telemóvel", "objects"),
    "(SO)": ("⚽", "Bola de Futebol", "objects"),
    "(so)": ("⚽", "Bola de Futebol", "objects"),
    "(PI)": ("🍕", "Pizza", "objects"),
    "(pi)": ("🍕", "Pizza", "objects"),
    "(AU)": ("🚗", "Carro", "objects"),
    "(au)": ("🚗", "Carro", "objects"),
    "(UM)": ("☂️", "Guarda-chuva", "objects"),
    "(um)": ("☂️", "Guarda-chuva", "objects"),
}


def parse_emoticons_to_html(text: str) -> str:
    """Replaces MSN emoticon shortcuts in text with styled HTML emojis."""
    # Escape HTML special characters first (except our substitutions)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Sort shortcuts by length descending so multi-character like (MP) matches before (M)
    sorted_shortcuts = sorted(MSN_EMOTICONS.keys(), key=lambda k: len(k), reverse=True)

    for sc in sorted_shortcuts:
        emoji, desc, _ = MSN_EMOTICONS[sc]
        pattern = re.escape(sc)
        replacement = f'<span style="font-size: 16px; font-family: \'Segoe UI Emoji\', \'Apple Color Emoji\', sans-serif;" title="{desc}">{emoji}</span>'
        text = re.sub(pattern, replacement, text)

    return text


import base64
import io
import os
import re
from typing import Dict, List, Tuple
from PyQt6.QtGui import QColor, QPainter, QPixmap, QBrush, QPen, QFont, QPainterPath, QImage
from PyQt6.QtCore import Qt, QRectF, QByteArray, QBuffer, QIODevice


# Predefined Classic MSN Avatar Themes
AVATAR_PRESETS: Dict[str, Dict[str, str]] = {
    "avatar_1": {"name": "Borboleta MSN", "emoji": "🦋", "bg": "#00A859", "accent": "#008040"},
    "avatar_2": {"name": "Skater Boy", "emoji": "🛹", "bg": "#E67E22", "accent": "#D35400"},
    "avatar_3": {"name": "Gamer Retro", "emoji": "🎮", "bg": "#8E44AD", "accent": "#6C3483"},
    "avatar_4": {"name": "Pato de Borracha", "emoji": "🦆", "bg": "#F1C40F", "accent": "#F39C12"},
    "avatar_5": {"name": "Guitarra Rock", "emoji": "🎸", "bg": "#E74C3C", "accent": "#C0392B"},
    "avatar_6": {"name": "Cachorrinho", "emoji": "🐶", "bg": "#3498DB", "accent": "#2980B9"},
    "avatar_7": {"name": "Gatinho Fofo", "emoji": "🐱", "bg": "#1ABC9C", "accent": "#16A085"},
    "avatar_8": {"name": "Futebol 10", "emoji": "⚽", "bg": "#2C3E50", "accent": "#1A252F"},
    "avatar_9": {"name": "Coração MSN", "emoji": "💖", "bg": "#FF69B4", "accent": "#C71585"},
    "avatar_10": {"name": "Alien Verde", "emoji": "👽", "bg": "#27AE60", "accent": "#1E8449"},
    "avatar_11": {"name": "Estrela Pop", "emoji": "⭐", "bg": "#F39C12", "accent": "#B9770E"},
    "avatar_12": {"name": "Robô Live", "emoji": "🤖", "bg": "#34495E", "accent": "#212F3D"},
}


def encode_image_file_to_avatar_str(filepath: str, max_size: int = 160) -> str:
    """Loads a user photograph, center-crops/scales it to a square, and encodes it as base64."""
    img = QImage(filepath)
    if img.isNull():
        return "avatar_1"

    # Square crop
    min_dim = min(img.width(), img.height())
    x = (img.width() - min_dim) // 2
    y = (img.height() - min_dim) // 2
    cropped = img.copy(x, y, min_dim, min_dim)
    scaled = cropped.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    scaled.save(buf, "JPEG", 85)
    b64 = ba.toBase64().data().decode("ascii")
    return f"custom:{b64}"


def generate_avatar_pixmap(avatar_id: str = "avatar_1", size: int = 64) -> QPixmap:
    """Generates a rounded high-resolution QPixmap avatar with glossy border, supporting custom photos."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    rect = QRectF(2, 2, size - 4, size - 4)

    # Check if this is a custom user photograph
    if avatar_id and avatar_id.startswith("custom:"):
        b64_str = avatar_id[len("custom:"):]
        try:
            raw_bytes = base64.b64decode(b64_str)
            custom_img = QImage.fromData(raw_bytes)
            if not custom_img.isNull():
                path = QPainterPath()
                path.addRoundedRect(rect, 10, 10)
                painter.save()
                painter.setClipPath(path)
                scaled_img = custom_img.scaled(int(rect.width()), int(rect.height()), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                painter.drawImage(rect.toRect(), scaled_img)
                painter.restore()

                # Border and gloss
                painter.setPen(QPen(QColor("#7eaed3"), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect, 10, 10)

                highlight_rect = QRectF(4, 4, size - 8, (size - 8) / 2.2)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 45)))
                painter.drawRoundedRect(highlight_rect, 8, 8)

                painter.end()
                return pixmap
        except Exception:
            pass

    # Preset avatar fallback
    preset = AVATAR_PRESETS.get(avatar_id, AVATAR_PRESETS["avatar_1"])
    bg_color = QColor(preset["bg"])
    accent_color = QColor(preset["accent"])

    # Rounded background rectangle
    painter.setPen(QPen(accent_color, 2))
    painter.setBrush(QBrush(bg_color))
    painter.drawRoundedRect(rect, 10, 10)

    # Glossy top highlight
    highlight_rect = QRectF(4, 4, size - 8, (size - 8) / 2.2)
    gloss_color = QColor(255, 255, 255, 60)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gloss_color))
    painter.drawRoundedRect(highlight_rect, 8, 8)

    # Draw Emoji Icon
    font_size = int(size * 0.48)
    font = QFont("Segoe UI Emoji", font_size)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, preset["emoji"])

    painter.end()
    return pixmap
