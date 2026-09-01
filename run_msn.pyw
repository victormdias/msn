"""
Windows Live / MSN Messenger (Sem Consola / No Console Window)
Pode ser executado com duplo clique direto no Windows sem abrir a linha de comandos (Shell).
"""
import sys
import os
import argparse
import traceback

# Add current workspace to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Windows Live Messenger")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço do servidor")
    parser.add_argument("--port", type=int, default=8800, help="Porta do servidor")
    args = parser.parse_args()

    try:
        from msn.client.app import MSNClientApp
        client = MSNClientApp(host=args.host, port=args.port)
        sys.exit(client.run())
    except Exception as e:
        # Show error in dialog if pythonw fails
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Erro ao iniciar o MSN Messenger:\n\n{traceback.format_exc()}", "MSN Messenger - Erro", 0x10)
        except Exception:
            pass