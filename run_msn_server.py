"""
Entry point to run the MSN Messenger Central Server (Local or 24/7 Cloud)
"""
import os
import sys
import argparse
from msn.server.msn_server import run_server_standalone

if __name__ == "__main__":
    env_port = int(os.environ.get("PORT", 8800))
    env_host = os.environ.get("HOST", "0.0.0.0")

    parser = argparse.ArgumentParser(description="MSN Messenger WebSocket Server")
    parser.add_argument("--host", default=env_host, help="Host address to bind")
    parser.add_argument("--port", type=int, default=env_port, help="Port number")
    parser.add_argument("--no-bots", action="store_true", help="Disable simulated bot friends")
    args = parser.parse_args()

    enable_bots = not args.no_bots
    print("==================================================")
    print(" 🦋 MSN Messenger Server (Windows Live Messenger)")
    print(f" Servidor Online: ws://{args.host}:{args.port}")
    print(f" Amigos Virtuais (Bots): {'Ativados' if enable_bots else 'Desativados (Apenas Pessoas Reais)'}")
    print("==================================================")
    run_server_standalone(host=args.host, port=args.port, enable_bots=enable_bots)