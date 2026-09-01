"""
MSN Messenger (Windows Live Messenger)
Principal Ponto de Entrada da Aplicação
Inicia o servidor se necessário e abre o ecrã oficial de Registo e Início de Sessão.
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

    print("=========================================================")
    print(" 🦋 Windows Live Messenger (MSN Messenger em Python)")
    print(f" A ligar a: {args.host}:{args.port}")
    print("=========================================================")

    try:
        from msn.client.app import MSNClientApp
        client = MSNClientApp(host=args.host, port=args.port)
        sys.exit(client.run())
    except Exception as e:
        traceback.print_exc()
        input("Pressione Enter para sair...")
