"""
Protocol definitions for MSN Messenger (Python Edition)
Contains action types, user statuses, message payloads, and JSON serialization.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import time
from typing import Any, Dict, List, Optional


class UserStatus(str, Enum):
    ONLINE = "online"         # Disponível 🟢
    BUSY = "busy"             # Ocupado 🔴
    BRB = "brb"               # Volto já 🕒
    AWAY = "away"             # Ausente 🟡
    PHONE = "phone"           # Ao telefone 📞
    LUNCH = "lunch"           # A almoçar 🍽️
    INVISIBLE = "invisible"   # Invisível ⚪
    OFFLINE = "offline"       # Desligado ⚫

    @property
    def label_pt(self) -> str:
        labels = {
            UserStatus.ONLINE: "Disponível",
            UserStatus.BUSY: "Ocupado",
            UserStatus.BRB: "Volto já",
            UserStatus.AWAY: "Ausente",
            UserStatus.PHONE: "Ao telefone",
            UserStatus.LUNCH: "A almoçar",
            UserStatus.INVISIBLE: "Invisível",
            UserStatus.OFFLINE: "Desligado",
        }
        return labels.get(self, "Desligado")

    @property
    def icon_char(self) -> str:
        icons = {
            UserStatus.ONLINE: "🟢",
            UserStatus.BUSY: "🔴",
            UserStatus.BRB: "🕒",
            UserStatus.AWAY: "🟡",
            UserStatus.PHONE: "📞",
            UserStatus.LUNCH: "🍽️",
            UserStatus.INVISIBLE: "⚪",
            UserStatus.OFFLINE: "⚫",
        }
        return icons.get(self, "⚫")

    @property
    def color_hex(self) -> str:
        colors = {
            UserStatus.ONLINE: "#2ecc71",
            UserStatus.BUSY: "#e74c3c",
            UserStatus.BRB: "#f39c12",
            UserStatus.AWAY: "#f1c40f",
            UserStatus.PHONE: "#9b59b6",
            UserStatus.LUNCH: "#e67e22",
            UserStatus.INVISIBLE: "#95a5a6",
            UserStatus.OFFLINE: "#7f8c8d",
        }
        return colors.get(self, "#7f8c8d")


class MsgAction(str, Enum):
    # Authentication & Session
    REGISTER_REQ = "register_req"
    REGISTER_RES = "register_res"
    LOGIN_REQ = "login_req"
    LOGIN_RES = "login_res"
    LOGOUT = "logout"

    # Profile & Presence
    STATUS_UPDATE = "status_update"
    PROFILE_UPDATE = "profile_update"
    CONTACT_STATUS_CHANGED = "contact_status_changed"

    # Contacts Management
    GET_CONTACTS = "get_contacts"
    CONTACTS_LIST = "contacts_list"
    ADD_CONTACT_REQ = "add_contact_req"
    ADD_CONTACT_RES = "add_contact_res"
    REMOVE_CONTACT = "remove_contact"
    BLOCK_CONTACT = "block_contact"

    # Direct Messaging (Chat)
    SEND_MSG = "send_msg"
    RECV_MSG = "recv_msg"
    TYPING_NOTIFY = "typing_notify"

    # MSN Iconic Features
    NUDGE = "nudge"                         # Chamar a atenção (Zumbido / Tremer de ecrã)
    WINK = "wink"                           # Animação Winks do MSN
    VOICE_CLIP = "voice_clip"               # Mensagem de áudio curta
    VIDEO_FRAME = "video_frame"             # Transmissão de frame de webcam em tempo real
    VIDEO_TOGGLE = "video_toggle"           # Ligar / desligar vídeo
    FILE_TRANSFER_START = "file_start"      # Envio de ficheiro
    FILE_TRANSFER_CHUNK = "file_chunk"
    FILE_TRANSFER_FINISH = "file_finish"
    FILE_TRANSFER_REJECT = "file_reject"

    # Interactive Mini-Games
    GAME_INVITE = "game_invite"
    GAME_RESPONSE = "game_response"
    GAME_MOVE = "game_move"
    GAME_END = "game_end"

    # System & Heartbeat
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class UserProfile:
    email: str
    nickname: str
    status: UserStatus = UserStatus.ONLINE
    personal_msg: str = ""                  # "O que está a ouvir? 🎵..."
    avatar_id: str = "avatar_1"
    group: str = "Amigos"
    custom_avatar_b64: Optional[str] = None
    is_bot: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, UserStatus) else str(self.status)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        status_val = data.get("status", UserStatus.OFFLINE.value)
        try:
            status = UserStatus(status_val)
        except ValueError:
            status = UserStatus.OFFLINE

        return cls(
            email=data.get("email", ""),
            nickname=data.get("nickname", data.get("email", "")),
            status=status,
            personal_msg=data.get("personal_msg", ""),
            avatar_id=data.get("avatar_id", "avatar_1"),
            group=data.get("group", "Amigos"),
            custom_avatar_b64=data.get("custom_avatar_b64"),
            is_bot=data.get("is_bot", False)
        )


@dataclass
class Packet:
    action: MsgAction
    sender: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps({
            "action": self.action.value if isinstance(self.action, MsgAction) else str(self.action),
            "sender": self.sender,
            "target": self.target,
            "payload": self.payload,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, json_str: str) -> "Packet":
        d = json.loads(json_str)
        try:
            action = MsgAction(d["action"])
        except ValueError:
            action = MsgAction.ERROR

        return cls(
            action=action,
            sender=d.get("sender", ""),
            target=d.get("target", ""),
            payload=d.get("payload", {}),
            timestamp=d.get("timestamp", time.time())
        )
