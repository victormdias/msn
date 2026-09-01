"""
Entry point to run the MSN Messenger Desktop Client (PyQt6)
"""
import sys
import argparse
from msn.client.app import MSNClientApp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MSN Messenger Client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8800, help="Server port")
    args = parser.parse_args()

    client = MSNClientApp(host=args.host, port=args.port)
    sys.exit(client.run())