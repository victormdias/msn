"""
MSN Messenger Central WebSocket Server
Handles user authentication, contact lists, presence updates, instant messaging,
nudges, interactive games (Tic-Tac-Toe), file relay, and bot buddy interactions.
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Optional
import websockets
from websockets.server import WebSocketServerProtocol

from msn.common.protocol import UserProfile, UserStatus, MsgAction, Packet
from msn.server.bot_friends import MSNBotController, BOT_PROFILES
from msn.server.database import MSNDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MSN Server] %(message)s")
logger = logging.getLogger("MSNServer")


class MSNServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8800, enable_bots: bool = True, db_path: str = "msn_data.db"):
        self.host = host
        self.port = port
        self.enable_bots = enable_bots
        self.bot_controller = MSNBotController() if enable_bots else None
        self.db = MSNDatabase(db_path=db_path)

        # Connected active sockets: email -> WebSocketServerProtocol
        self.clients: Dict[str, WebSocketServerProtocol] = {}

        # User profiles in memory: email -> UserProfile
        self.users: Dict[str, UserProfile] = {}

        # Mini-game sessions: session_id -> dict
        self.game_sessions: Dict[str, dict] = {}

        # Initialize default bots if enabled
        if self.enable_bots:
            for b in BOT_PROFILES:
                self.users[b.email] = b
                self.db.register_user(b.email, "bot_pass_123", b.nickname, b.avatar_id, b.personal_msg)

    async def start(self):
        logger.info(f"Starting MSN Messenger Server on ws://{self.host}:{self.port} ...")
        async with websockets.serve(self._handle_client, self.host, self.port):
            logger.info("MSN Messenger Server is ONLINE and accepting connections.")
            await asyncio.Future()  # run forever

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        current_user_email: Optional[str] = None
        try:
            async for raw_message in websocket:
                try:
                    packet = Packet.from_json(raw_message)
                    action = packet.action
                    sender = packet.sender
                    target = packet.target
                    payload = packet.payload

                    if action == MsgAction.REGISTER_REQ:
                        email = payload.get("email", "").strip().lower()
                        password = payload.get("password", "")
                        nickname = payload.get("nickname", email.split("@")[0])
                        avatar_id = payload.get("avatar_id", "avatar_1")
                        personal_msg = payload.get("personal_msg", "")

                        success, msg = self.db.register_user(
                            email=email,
                            password=password,
                            nickname=nickname,
                            avatar_id=avatar_id,
                            personal_msg=personal_msg
                        )

                        if success:
                            logger.info(f"New user registered: {email} ({nickname})")

                        res = Packet(
                            action=MsgAction.REGISTER_RES,
                            sender="server",
                            target=email,
                            payload={"success": success, "message": msg}
                        )
                        await websocket.send(res.to_json())

                    elif action == MsgAction.LOGIN_REQ:
                        email = payload.get("email", "").strip().lower()
                        password = payload.get("password", "")
                        nickname = payload.get("nickname", "")
                        status_str = payload.get("status", UserStatus.ONLINE.value)
                        avatar_id = payload.get("avatar_id", "")
                        personal_msg = payload.get("personal_msg", "")

                        # Authenticate via Database
                        auth_ok, db_profile, auth_msg = self.db.authenticate_user(email, password)

                        if not auth_ok:
                            # Auto-register on first login if no users exist or if password is provided
                            if not self.db.get_user_profile(email):
                                reg_nick = nickname or email.split("@")[0]
                                self.db.register_user(email, password or "123456", reg_nick, avatar_id or "avatar_1", personal_msg)
                                auth_ok, db_profile, auth_msg = self.db.authenticate_user(email, password or "123456")

                        if not auth_ok or not db_profile:
                            res = Packet(
                                action=MsgAction.LOGIN_RES,
                                sender="server",
                                target=email,
                                payload={"success": False, "message": auth_msg}
                            )
                            await websocket.send(res.to_json())
                            continue

                        current_user_email = email
                        self.clients[email] = websocket

                        # Update profile status & custom updates (preserve DB saved profile)
                        status = UserStatus(status_str) if status_str in [s.value for s in UserStatus] else UserStatus.ONLINE
                        db_profile.status = status
                        if nickname and not db_profile.nickname:
                            db_profile.nickname = nickname
                        if avatar_id and not db_profile.avatar_id:
                            db_profile.avatar_id = avatar_id
                        if personal_msg and not db_profile.personal_msg:
                            db_profile.personal_msg = personal_msg

                        self.users[email] = db_profile
                        self.db.update_user_profile(email, db_profile.nickname, db_profile.avatar_id, db_profile.personal_msg)

                        # If bots enabled, ensure default bot friends are available
                        contacts_data = self.db.get_contacts_for_user(email)
                        if self.enable_bots:
                            existing_contact_emails = {c.email for c in contacts_data}
                            for b in BOT_PROFILES:
                                if b.email not in existing_contact_emails:
                                    self.db.add_contact(email, b.email, b.group)
                            contacts_data = self.db.get_contacts_for_user(email)

                        # Update real-time status of loaded contacts
                        for c in contacts_data:
                            if c.email in self.clients:
                                c.status = self.users.get(c.email, c).status
                            elif self.enable_bots and c.email in self.bot_controller.bots:
                                c.status = self.bot_controller.bots[c.email].status
                            else:
                                c.status = UserStatus.OFFLINE

                        # Send login success response
                        res = Packet(
                            action=MsgAction.LOGIN_RES,
                            sender="server",
                            target=email,
                            payload={
                                "success": True,
                                "profile": db_profile.to_dict(),
                                "contacts": [c.to_dict() for c in contacts_data]
                            }
                        )
                        await websocket.send(res.to_json())

                        # Broadcast online presence to all users who have this user in their contact list
                        await self._broadcast_presence(email)
                        logger.info(f"User signed in: {email} ({db_profile.nickname}) - Status: {status.name}")

                    elif action == MsgAction.STATUS_UPDATE:
                        if current_user_email and current_user_email in self.users:
                            new_status_str = payload.get("status", UserStatus.ONLINE.value)
                            new_status = UserStatus(new_status_str) if new_status_str in [s.value for s in UserStatus] else UserStatus.ONLINE
                            self.users[current_user_email].status = new_status
                            if "personal_msg" in payload:
                                self.users[current_user_email].personal_msg = payload["personal_msg"]
                            if "nickname" in payload:
                                self.users[current_user_email].nickname = payload["nickname"]
                            if "avatar_id" in payload:
                                self.users[current_user_email].avatar_id = payload["avatar_id"]

                            self.db.update_user_profile(
                                current_user_email,
                                nickname=self.users[current_user_email].nickname,
                                avatar_id=self.users[current_user_email].avatar_id,
                                personal_msg=self.users[current_user_email].personal_msg
                            )

                            await self._broadcast_presence(current_user_email)

                    elif action == MsgAction.SEND_MSG:
                        # Instant message relay
                        text = payload.get("text", "")
                        color = payload.get("color", "#000000")
                        font = payload.get("font", "Segoe UI")
                        bold = payload.get("bold", False)
                        italic = payload.get("italic", False)

                        # Check if target is a bot
                        if self.enable_bots and target in self.bot_controller.bots:
                            # Echo message to target bot and schedule bot auto-reply
                            asyncio.create_task(self._process_bot_message_async(target, sender, text))
                        elif target in self.clients:
                            target_ws = self.clients[target]
                            out_packet = Packet(
                                action=MsgAction.RECV_MSG,
                                sender=sender,
                                target=target,
                                payload={
                                    "text": text,
                                    "color": color,
                                    "font": font,
                                    "bold": bold,
                                    "italic": italic,
                                    "timestamp": packet.timestamp
                                }
                            )
                            await target_ws.send(out_packet.to_json())

                    elif action == MsgAction.TYPING_NOTIFY:
                        # Forward typing indicator to target
                        if target in self.clients:
                            await self.clients[target].send(packet.to_json())

                    elif action == MsgAction.NUDGE:
                        # MSN Nudge relay
                        if self.enable_bots and target in self.bot_controller.bots:
                            asyncio.create_task(self._process_bot_nudge_async(target, sender))
                        elif target in self.clients:
                            await self.clients[target].send(packet.to_json())

                    elif (action == MsgAction.VOICE_CLIP or action == MsgAction.VIDEO_FRAME 
                          or action == MsgAction.VIDEO_TOGGLE or action == MsgAction.FILE_TRANSFER_START 
                          or action == MsgAction.FILE_TRANSFER_CHUNK or action == MsgAction.FILE_TRANSFER_FINISH):
                        # Forward multimedia payload
                        if target in self.clients:
                            await self.clients[target].send(packet.to_json())

                    elif action == MsgAction.ADD_CONTACT_REQ:
                        new_contact_email = payload.get("email", "").strip().lower()
                        group = payload.get("group", "Amigos")
                        if current_user_email and new_contact_email:
                            self.db.add_contact(current_user_email, new_contact_email, group)
                            self.db.add_contact(new_contact_email, current_user_email, "Amigos")

                            contact_profile = self.db.get_user_profile(new_contact_email)
                            if not contact_profile:
                                contact_profile = UserProfile(
                                    email=new_contact_email,
                                    nickname=new_contact_email.split("@")[0],
                                    status=UserStatus.OFFLINE
                                )
                            else:
                                if new_contact_email in self.clients:
                                    contact_profile.status = self.users.get(new_contact_email, contact_profile).status
                                else:
                                    contact_profile.status = UserStatus.OFFLINE

                            res = Packet(
                                action=MsgAction.ADD_CONTACT_RES,
                                sender="server",
                                target=current_user_email,
                                payload={"success": True, "contact": contact_profile.to_dict()}
                            )
                            await websocket.send(res.to_json())

                            # Notify the added contact if online so both see each other immediately
                            if new_contact_email in self.clients:
                                my_profile = self.users.get(current_user_email)
                                if my_profile:
                                    await self.clients[new_contact_email].send(Packet(
                                        action=MsgAction.ADD_CONTACT_RES,
                                        sender="server",
                                        target=new_contact_email,
                                        payload={"success": True, "contact": my_profile.to_dict()}
                                    ).to_json())

                    # Interactive Mini-Games
                    elif action == MsgAction.GAME_INVITE:
                        game_type = payload.get("game_type", "tictactoe")
                        session_id = f"{min(sender, target)}_{max(sender, target)}_{game_type}"
                        self.game_sessions[session_id] = {
                            "session_id": session_id,
                            "game_type": game_type,
                            "p1": sender,
                            "p2": target,
                            "board": [""] * 9,
                            "turn": sender,
                            "status": "pending"
                        }
                        if self.enable_bots and target in self.bot_controller.bots:
                            # Bot accepts game invite immediately!
                            self.game_sessions[session_id]["status"] = "active"
                            accept_pkt = Packet(
                                action=MsgAction.GAME_RESPONSE,
                                sender=target,
                                target=sender,
                                payload={"session_id": session_id, "accepted": True, "p1": sender, "p2": target}
                            )
                            await websocket.send(accept_pkt.to_json())
                        elif target in self.clients:
                            await self.clients[target].send(packet.to_json())

                    elif action == MsgAction.GAME_RESPONSE:
                        accepted = payload.get("accepted", False)
                        session_id = payload.get("session_id", "")
                        if session_id in self.game_sessions:
                            if accepted:
                                self.game_sessions[session_id]["status"] = "active"
                            else:
                                del self.game_sessions[session_id]
                        if target in self.clients:
                            await self.clients[target].send(packet.to_json())

                    elif action == MsgAction.GAME_MOVE:
                        session_id = payload.get("session_id", "")
                        cell_idx = payload.get("cell_idx", -1)
                        mark = payload.get("mark", "X")
                        if session_id in self.game_sessions:
                            sess = self.game_sessions[session_id]
                            if 0 <= cell_idx < 9 and sess["board"][cell_idx] == "":
                                sess["board"][cell_idx] = mark
                                next_turn = sess["p2"] if sender == sess["p1"] else sess["p1"]
                                sess["turn"] = next_turn

                                # Forward move to human opponent
                                if target in self.clients:
                                    await self.clients[target].send(Packet(
                                        action=MsgAction.GAME_MOVE,
                                        sender=sender,
                                        target=target,
                                        payload={"session_id": session_id, "cell_idx": cell_idx, "mark": mark, "turn": next_turn}
                                    ).to_json())

                                # If target is a bot, bot calculates move
                                if self.enable_bots and target in self.bot_controller.bots:
                                    asyncio.create_task(self._process_bot_game_move_async(session_id, target, sender))

                except Exception as ex:
                    logger.error(f"Error processing packet: {ex}", exc_info=True)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if current_user_email and current_user_email in self.clients:
                del self.clients[current_user_email]
                if current_user_email in self.users:
                    self.users[current_user_email].status = UserStatus.OFFLINE
                    await self._broadcast_presence(current_user_email)
                logger.info(f"User disconnected: {current_user_email}")

    def _get_contacts_for_user(self, email: str) -> List[UserProfile]:
        contact_emails = self.user_contacts.get(email, set())
        contacts = []
        for c_email in contact_emails:
            if c_email in self.users:
                # If connected client is offline
                prof = self.users[c_email]
                if not prof.is_bot and c_email not in self.clients:
                    prof.status = UserStatus.OFFLINE
                contacts.append(prof)
            else:
                contacts.append(UserProfile(
                    email=c_email,
                    nickname=c_email.split("@")[0],
                    status=UserStatus.OFFLINE
                ))
        return contacts

    async def _broadcast_presence(self, email: str):
        """Sends presence update packet to all clients who have this user as a contact."""
        profile = self.users.get(email)
        if not profile:
            return

        pkt = Packet(
            action=MsgAction.CONTACT_STATUS_CHANGED,
            sender="server",
            payload={"contact": profile.to_dict()}
        )

        for other_email, ws in list(self.clients.items()):
            if other_email == email:
                continue
            contacts = self.user_contacts.get(other_email, set())
            if email in contacts or True:  # Broadcast to all connected buddies
                try:
                    await ws.send(pkt.to_json())
                except Exception:
                    pass

    async def _process_bot_message_async(self, bot_email: str, sender_email: str, text: str):
        """Simulates realistic typing delay before bot replies."""
        await asyncio.sleep(0.8 + len(text) * 0.02)
        if sender_email in self.clients:
            # Send typing notification
            await self.clients[sender_email].send(Packet(
                action=MsgAction.TYPING_NOTIFY,
                sender=bot_email,
                target=sender_email,
                payload={"is_typing": True}
            ).to_json())

            await asyncio.sleep(1.2)
            replies = self.bot_controller.handle_message(bot_email, sender_email, text)
            for r in replies:
                await self.clients[sender_email].send(r.to_json())

    async def _process_bot_nudge_async(self, bot_email: str, sender_email: str):
        """Processes bot reaction to Nudge with small delay."""
        await asyncio.sleep(0.7)
        if sender_email in self.clients:
            replies = self.bot_controller.handle_nudge(bot_email, sender_email)
            for r in replies:
                await self.clients[sender_email].send(r.to_json())

    async def _process_bot_game_move_async(self, session_id: str, bot_email: str, sender_email: str):
        """Calculates and sends bot's Tic-Tac-Toe move after slight think delay."""
        await asyncio.sleep(1.0)
        if session_id not in self.game_sessions:
            return
        sess = self.game_sessions[session_id]
        bot_idx = self.bot_controller.handle_bot_game_move(sess["board"], bot_mark="O")
        if 0 <= bot_idx < 9:
            sess["board"][bot_idx] = "O"
            sess["turn"] = sender_email
            if sender_email in self.clients:
                await self.clients[sender_email].send(Packet(
                    action=MsgAction.GAME_MOVE,
                    sender=bot_email,
                    target=sender_email,
                    payload={"session_id": session_id, "cell_idx": bot_idx, "mark": "O", "turn": sender_email}
                ).to_json())


def run_server_standalone(host: str = "0.0.0.0", port: int = 8800, enable_bots: bool = True):
    server = MSNServer(host=host, port=port, enable_bots=enable_bots)
    asyncio.run(server.start())


if __name__ == "__main__":
    run_server_standalone()
