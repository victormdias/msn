"""
MSN Messenger Client Application Coordinator
Handles login flow, theme loading, and transitions to main window.
"""
import os
import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from msn.common.protocol import UserProfile, UserStatus
from msn.client.theme import MSN_QSS
from msn.client.network import MSNNetworkClient
from msn.client.gui.login_window import MSNLoginWindow
from msn.client.gui.main_window import MSNMainWindow


import socket
import threading
import asyncio
from msn.server.msn_server import MSNServer

class MSNClientApp:
    def __init__(self, host: str = "127.0.0.1", port: int = 8800):
        self.host = host
        self.port = port

        # Ensure server is running
        self._ensure_server_running()

        self.network = MSNNetworkClient(host=host, port=port)

        self.login_window: Optional[MSNLoginWindow] = None
        self.main_window: Optional[MSNMainWindow] = None

        self.cached_login_info = {}

    def _ensure_server_running(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            result = s.connect_ex((self.host, self.port))
            s.close()
            if result != 0:
                # Port is not open, start background server
                def _run():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    server = MSNServer(host="0.0.0.0", port=self.port, enable_bots=True)
                    loop.run_until_complete(server.start())

                t = threading.Thread(target=_run, daemon=True)
                t.start()

                # Wait for server to accept connections
                for _ in range(30):
                    time.sleep(0.05)
                    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s2.settimeout(0.2)
                    ok = s2.connect_ex((self.host, self.port))
                    s2.close()
                    if ok == 0:
                        break
        except Exception:
            pass

    def run(self):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("windows.live.messenger.msn")
        except Exception:
            pass

        app = QApplication.instance() or QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setStyleSheet(MSN_QSS)

        # Set App-wide window icon to logo.png
        possible_logo_paths = [
            os.path.abspath("logo.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logo.png"),
        ]
        logo_file = next((p for p in possible_logo_paths if os.path.exists(p)), None)
        if logo_file:
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(logo_file))

        # Start background network thread
        self.network.start_client()
        self.network.sig_register_response.connect(self._on_register_response)
        self.network.sig_login_response.connect(self._on_login_response)
        self.network.sig_disconnected.connect(self._on_network_disconnected)

        # Show Login Window
        self.login_window = MSNLoginWindow()
        self.login_window.sig_login_requested.connect(self._on_login_requested)
        self.login_window.sig_register_requested.connect(self._on_register_requested)
        self.login_window.show()

        return app.exec()

    def _on_register_requested(self, email: str, pwd: str, nick: str, avatar_id: str, personal_msg: str):
        self.network.register(email, pwd, nick, avatar_id, personal_msg)

    def _on_register_response(self, success: bool, message: str):
        if self.login_window:
            self.login_window.handle_register_response(success, message)

    def _on_login_requested(self, email: str, pwd: str, nick: str, status: UserStatus, avatar_id: str, personal_msg: str, server_addr: str = "127.0.0.1:8800"):
        server_addr = server_addr.strip()
        if server_addr.startswith("wss://") or server_addr.startswith("ws://"):
            target_uri = server_addr
        elif any(c in server_addr for c in [".onrender.com", ".railway.app", ".fly.dev", ".koyeb.app", ".herokuapp.com"]):
            target_uri = f"wss://{server_addr}"
        elif ":" in server_addr:
            host, port_str = server_addr.split(":", 1)
            port = int(port_str) if port_str.isdigit() else 8800
            target_uri = f"ws://{host}:{port}"
        else:
            target_uri = f"ws://{server_addr}:8800"

        self.network.uri = target_uri

        self.cached_login_info = {
            "email": email,
            "nick": nick,
            "status": status,
            "avatar_id": avatar_id,
            "personal_msg": personal_msg
        }
        self.network.login(email, pwd, nick, status, avatar_id, personal_msg)

    def _on_login_response(self, success: bool, profile_dict: dict, contacts_list: list, message: str = ""):
        if success:
            if self.main_window and self.main_window.isVisible():
                return

            if self.main_window:
                self.main_window.close()
                self.main_window = None

            profile = UserProfile.from_dict(profile_dict)
            contacts = [UserProfile.from_dict(c) for c in contacts_list]

            self.main_window = MSNMainWindow(profile, contacts, self.network)
            self.main_window.show_slide_up_from_tray()

            if self.login_window:
                self.login_window.hide()
        else:
            if self.login_window:
                err = message or "Palavra-passe incorreta ou erro de servidor."
                self.login_window.on_login_failed(err)

    def _on_network_disconnected(self, err: str):
        pass
