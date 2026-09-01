"""
MSN Messenger PyQt6 Network Client
Async WebSocket client running in a QThread, dispatching signals to the Qt GUI thread.
"""
import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional
import websockets
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from msn.common.protocol import UserProfile, UserStatus, MsgAction, Packet

logger = logging.getLogger("MSNNetwork")


class MSNNetworkClient(QObject):
    # Qt Signals for GUI
    sig_connected = pyqtSignal()
    sig_disconnected = pyqtSignal(str)
    sig_register_response = pyqtSignal(bool, str)             # success, message
    sig_login_response = pyqtSignal(bool, dict, list, str)    # success, profile_dict, contacts_list, message
    sig_contact_status_changed = pyqtSignal(dict)              # contact_dict
    sig_message_received = pyqtSignal(str, dict, float)        # sender, payload, timestamp
    sig_typing_received = pyqtSignal(str, bool)                # sender, is_typing
    sig_nudge_received = pyqtSignal(str)                       # sender
    sig_game_invite = pyqtSignal(str, dict)                    # sender, payload
    sig_game_response = pyqtSignal(str, dict)                  # sender, payload
    sig_game_move = pyqtSignal(str, dict)                      # sender, payload
    sig_voice_clip_received = pyqtSignal(str, bytes)           # sender, wav_bytes
    sig_video_frame_received = pyqtSignal(str, str)            # sender, b64_jpeg
    sig_video_toggle_received = pyqtSignal(str, bool)          # sender, enabled
    sig_contact_added = pyqtSignal(bool, dict)                 # success, contact_dict

    def __init__(self, host: str = "127.0.0.1", port: int = 8800):
        super().__init__()
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.ws = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._send_queue: Optional[asyncio.Queue] = None
        self.current_email = ""

    def start_client(self):
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run_event_loop)
        self._thread.start()

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._send_queue = asyncio.Queue()
        self._running = True
        self.loop.run_until_complete(self._main_network_loop())

    async def _main_network_loop(self):
        while self._running:
            try:
                async with websockets.connect(self.uri) as ws:
                    self.ws = ws
                    self.sig_connected.emit()
                    logger.info("Connected to MSN Server")

                    # If we had a pending login, queue it once
                    if self._pending_login_pkt:
                        pkt = self._pending_login_pkt
                        self._pending_login_pkt = None
                        self.send_packet(pkt)

                    # Run sender and receiver concurrently
                    recv_task = asyncio.create_task(self._receiver_loop())
                    send_task = asyncio.create_task(self._sender_loop())
                    done, pending = await asyncio.wait(
                        [recv_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
            except Exception as e:
                self.ws = None
                self.sig_disconnected.emit(str(e))
                await asyncio.sleep(1.5)  # Reconnect backoff

    async def _receiver_loop(self):
        if not self.ws:
            return
        async for raw_msg in self.ws:
            try:
                packet = Packet.from_json(raw_msg)
                action = packet.action
                sender = packet.sender
                payload = packet.payload

                if action == MsgAction.REGISTER_RES:
                    success = payload.get("success", False)
                    message = payload.get("message", "")
                    self.sig_register_response.emit(success, message)

                elif action == MsgAction.LOGIN_RES:
                    success = payload.get("success", False)
                    profile = payload.get("profile", {})
                    contacts = payload.get("contacts", [])
                    message = payload.get("message", "")
                    if success:
                        self._pending_login_pkt = None
                    self.sig_login_response.emit(success, profile, contacts, message)

                elif action == MsgAction.CONTACT_STATUS_CHANGED:
                    contact = payload.get("contact", {})
                    self.sig_contact_status_changed.emit(contact)

                elif action == MsgAction.RECV_MSG:
                    self.sig_message_received.emit(sender, payload, packet.timestamp)

                elif action == MsgAction.TYPING_NOTIFY:
                    is_typing = payload.get("is_typing", True)
                    self.sig_typing_received.emit(sender, is_typing)

                elif action == MsgAction.NUDGE:
                    self.sig_nudge_received.emit(sender)

                elif action == MsgAction.GAME_INVITE:
                    self.sig_game_invite.emit(sender, payload)

                elif action == MsgAction.GAME_RESPONSE:
                    self.sig_game_response.emit(sender, payload)

                elif action == MsgAction.GAME_MOVE:
                    self.sig_game_move.emit(sender, payload)

                elif action == MsgAction.VOICE_CLIP:
                    b64_data = payload.get("data", "")
                    if b64_data:
                        wav_bytes = base64.b64decode(b64_data)
                        self.sig_voice_clip_received.emit(sender, wav_bytes)

                elif action == MsgAction.VIDEO_FRAME:
                    b64_frame = payload.get("frame", "")
                    if b64_frame:
                        self.sig_video_frame_received.emit(sender, b64_frame)

                elif action == MsgAction.VIDEO_TOGGLE:
                    enabled = payload.get("enabled", False)
                    self.sig_video_toggle_received.emit(sender, enabled)

                elif action == MsgAction.ADD_CONTACT_RES:
                    success = payload.get("success", False)
                    contact = payload.get("contact", {})
                    self.sig_contact_added.emit(success, contact)

            except Exception as ex:
                logger.error(f"Error in network receiver: {ex}")

    async def _sender_loop(self):
        while self._running and self.ws:
            packet = await self._send_queue.get()
            try:
                if self.ws:
                    await self.ws.send(packet.to_json())
            except Exception as ex:
                logger.error(f"Error sending packet: {ex}")
                # Re-queue packet if failed
                await self._send_queue.put(packet)
                break
            finally:
                self._send_queue.task_done()

    def send_packet(self, packet: Packet):
        """Thread-safe dispatch from GUI thread into asyncio queue."""
        if self.loop and self._send_queue:
            asyncio.run_coroutine_threadsafe(self._send_queue.put(packet), self.loop)

    def register(self, email: str, password: str, nickname: str, avatar_id: str = "avatar_1", personal_msg: str = ""):
        pkt = Packet(
            action=MsgAction.REGISTER_REQ,
            sender=email,
            payload={
                "email": email,
                "password": password,
                "nickname": nickname,
                "avatar_id": avatar_id,
                "personal_msg": personal_msg
            }
        )
        self.send_packet(pkt)

    def login(self, email: str, password: str, nickname: str, status: UserStatus, avatar_id: str, personal_msg: str):
        self.current_email = email
        pkt = Packet(
            action=MsgAction.LOGIN_REQ,
            sender=email,
            payload={
                "email": email,
                "password": password,
                "nickname": nickname,
                "status": status.value,
                "avatar_id": avatar_id,
                "personal_msg": personal_msg
            }
        )
        if self.ws:
            self._pending_login_pkt = None
            self.send_packet(pkt)
        else:
            self._pending_login_pkt = pkt

    def update_presence(self, status: UserStatus, personal_msg: str = None, nickname: str = None, avatar_id: str = None):
        payload = {"status": status.value}
        if personal_msg is not None:
            payload["personal_msg"] = personal_msg
        if nickname is not None:
            payload["nickname"] = nickname
        if avatar_id is not None:
            payload["avatar_id"] = avatar_id

        pkt = Packet(
            action=MsgAction.STATUS_UPDATE,
            sender=self.current_email,
            payload=payload
        )
        self.send_packet(pkt)

    def send_message(self, target_email: str, text: str, color: str = "#000000", font: str = "Segoe UI", bold: bool = False, italic: bool = False):
        pkt = Packet(
            action=MsgAction.SEND_MSG,
            sender=self.current_email,
            target=target_email,
            payload={
                "text": text,
                "color": color,
                "font": font,
                "bold": bold,
                "italic": italic
            }
        )
        self.send_packet(pkt)

    def send_nudge(self, target_email: str):
        pkt = Packet(
            action=MsgAction.NUDGE,
            sender=self.current_email,
            target=target_email,
            payload={}
        )
        self.send_packet(pkt)

    def send_typing(self, target_email: str, is_typing: bool = True):
        pkt = Packet(
            action=MsgAction.TYPING_NOTIFY,
            sender=self.current_email,
            target=target_email,
            payload={"is_typing": is_typing}
        )
        self.send_packet(pkt)

    def send_voice_clip(self, target_email: str, wav_bytes: bytes):
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        pkt = Packet(
            action=MsgAction.VOICE_CLIP,
            sender=self.current_email,
            target=target_email,
            payload={"data": b64}
        )
        self.send_packet(pkt)

    def add_contact(self, contact_email: str):
        pkt = Packet(
            action=MsgAction.ADD_CONTACT_REQ,
            sender=self.current_email,
            payload={"email": contact_email}
        )
        self.send_packet(pkt)

    def send_game_invite(self, target_email: str, game_type: str = "tictactoe"):
        pkt = Packet(
            action=MsgAction.GAME_INVITE,
            sender=self.current_email,
            target=target_email,
            payload={"game_type": game_type}
        )
        self.send_packet(pkt)

    def send_game_response(self, target_email: str, session_id: str, accepted: bool):
        pkt = Packet(
            action=MsgAction.GAME_RESPONSE,
            sender=self.current_email,
            target=target_email,
            payload={"session_id": session_id, "accepted": accepted}
        )
        self.send_packet(pkt)

    def send_game_move(self, target_email: str, session_id: str, cell_idx: int, mark: str):
        pkt = Packet(
            action=MsgAction.GAME_MOVE,
            sender=self.current_email,
            target=target_email,
            payload={"session_id": session_id, "cell_idx": cell_idx, "mark": mark}
        )
        self.send_packet(pkt)

    def send_video_frame(self, target_email: str, b64_frame: str):
        pkt = Packet(
            action=MsgAction.VIDEO_FRAME,
            sender=self.current_email,
            target=target_email,
            payload={"frame": b64_frame}
        )
        self.send_packet(pkt)

    def send_video_toggle(self, target_email: str, enabled: bool):
        pkt = Packet(
            action=MsgAction.VIDEO_TOGGLE,
            sender=self.current_email,
            target=target_email,
            payload={"enabled": enabled}
        )
        self.send_packet(pkt)

    def close(self):
        self._running = False
        if self.loop:
            self.loop.stop()
