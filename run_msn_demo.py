"""
MSN Messenger All-In-One Launcher
Starts the embedded WebSocket Server in the background and opens the MSN Desktop Client immediately.
"""
import sys
import time
import threading
import asyncio
from msn.server.msn_server import MSNServer
from msn.client.app import MSNClientApp


def start_background_server(host="127.0.0.1", port=8800):
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = MSNServer(host=host, port=port, enable_bots=True)
        loop.run_until_complete(server.start())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.5)


if __name__ == "__main__":
    print("=======================================================")
    print(" 🦋 Windows Live Messenger (MSN Messenger em Python)")
    print(" A iniciar servidor em segundo plano e cliente gráfico...")
    print("=======================================================")
    start_background_server(host="127.0.0.1", port=8800)

    client = MSNClientApp(host="127.0.0.1", port=8800)
    sys.exit(client.run())