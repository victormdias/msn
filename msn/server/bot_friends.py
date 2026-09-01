"""
Simulated MSN Messenger Buddy Bots for interactive instant testing and nostalgia.
"""
import random
import time
from typing import Dict, List, Optional
from msn.common.protocol import UserProfile, UserStatus, MsgAction, Packet

BOT_PROFILES = [
    UserProfile(
        email="ana_martins@hotmail.com",
        nickname="~* Aninha *~ (L)",
        status=UserStatus.ONLINE,
        personal_msg="A ouvir: 🎵 Avril Lavigne - Complicated",
        avatar_id="avatar_1",
        group="Favoritos",
        is_bot=True
    ),
    UserProfile(
        email="carlos_skater@live.com",
        nickname="[xD] CaRLoS_90s [xD]",
        status=UserStatus.BUSY,
        personal_msg="A jogar Counter-Strike 1.6... nao chateiem! (H)",
        avatar_id="avatar_2",
        group="Amigos",
        is_bot=True
    ),
    UserProfile(
        email="marta_pop@msn.com",
        nickname="Martinha :: BRB ::",
        status=UserStatus.AWAY,
        personal_msg="Fui lanchar, volto já! (S)",
        avatar_id="avatar_9",
        group="Amigos",
        is_bot=True
    ),
    UserProfile(
        email="msn_assistente@bot.msn",
        nickname="🤖 MSN Helper Bot",
        status=UserStatus.ONLINE,
        personal_msg="Digita 'ajuda' para comandos e nostalgia!",
        avatar_id="avatar_12",
        group="Favoritos",
        is_bot=True
    ),
]


class MSNBotController:
    """Handles auto-responses and interactions for simulated bot friends."""

    def __init__(self):
        self.bots: Dict[str, UserProfile] = {b.email: b for b in BOT_PROFILES}
        self.game_sessions: Dict[str, Dict] = {}  # session_key -> state

    def handle_message(self, bot_email: str, sender_email: str, text: str) -> List[Packet]:
        """Generates intelligent, funny nostalgic MSN responses."""
        responses = []
        bot = self.bots.get(bot_email)
        if not bot:
            return responses

        text_lower = text.lower().strip()

        if bot_email == "msn_assistente@bot.msn":
            if "ajuda" in text_lower or "help" in text_lower:
                msg = (
                    "<b>🤖 Bem-vindo ao MSN Messenger!</b><br>"
                    "Comandos que podes testar:<br>"
                    "• <b>jogar</b>: Inicia uma partida de Jogo do Galo!<br>"
                    "• <b>piada</b>: Conta uma piada dos anos 2000.<br>"
                    "• <b>musica</b>: Altera a minha mensagem pessoal.<br>"
                    "• <b>nudge</b>: Carrega no botão ⚡ para me tremer a janela!<br>"
                    "• <b>emoticons</b>: Testa códigos como <code>:)</code>, <code>:D</code>, <code>(L)</code>, <code>(Y)</code>, <code>(6)</code>."
                )
            elif "piada" in text_lower:
                jokes = [
                    "O que é que o MSN disse para a Internet discada? 'Desliga isso que a minha mãe quer usar o telefone fixo!' :D",
                    "Porque é que o rapaz dos anos 2000 ficou horas a olhar para o monitor? Estava à espera que a rapariga ficasse online para pôr o status 'Ausente'! (H)",
                    "Sabias que 90% das conversas do MSN começavam com: 'olá td bem? add no orkut!' ;)",
                ]
                msg = random.choice(jokes)
            elif "jogar" in text_lower or "galo" in text_lower:
                msg = "Boa! Convidei-te para o Jogo do Galo! Clica no botão de Atividades 🎮 no topo do chat."
            else:
                msg = f"Recebi a tua mensagem: <i>'{text}'</i>! Tudo a funcionar impecavelmente no MSN! (Y)"

            responses.append(Packet(
                action=MsgAction.RECV_MSG,
                sender=bot_email,
                target=sender_email,
                payload={"text": msg, "color": "#008040", "font": "Segoe UI", "bold": False}
            ))

        elif bot_email == "ana_martins@hotmail.com":
            if any(w in text_lower for w in ["ola", "olá", "oi", "hey"]):
                msg = "Oiii! Tudo bem contigo?? Estava a ouvir música no Winamp (L)"
            elif "?" in text:
                msg = "Acho que sim! Mas espera aí que vou mudar o meu nick no MSN hehe :P"
            else:
                quotes = [
                    "Adoro esta música dos Evanescence! :D",
                    "Viste o episódio de Morangos com Açúcar ontem? (H)",
                    "Já tens o novo telemóvel com câmara? (MP)",
                    "Manda-me um toque depois para nos encontrarmos! ;)",
                ]
                msg = random.choice(quotes)

            responses.append(Packet(
                action=MsgAction.RECV_MSG,
                sender=bot_email,
                target=sender_email,
                payload={"text": msg, "color": "#c71585", "font": "Comic Sans MS", "bold": False}
            ))

        elif bot_email == "carlos_skater@live.com":
            msg = "Tou no meio de um round em de_dust2, já te respondo quando morrer! xD (H)"
            responses.append(Packet(
                action=MsgAction.RECV_MSG,
                sender=bot_email,
                target=sender_email,
                payload={"text": msg, "color": "#2980b9", "font": "Tahoma", "bold": True}
            ))

        return responses

    def handle_nudge(self, bot_email: str, sender_email: str) -> List[Packet]:
        """Bots react when nudged!"""
        responses = []
        if bot_email == "carlos_skater@live.com":
            msg = "Ei!! Quase morri no Counter-Strike por causa do teu Nudge a tremer tudo!! :@"
            color = "#c0392b"
        elif bot_email == "ana_martins@hotmail.com":
            msg = "Aaaaaah que susto! Toma lá de volta! ⚡"
            color = "#8e44ad"
            # Send a Nudge back!
            responses.append(Packet(
                action=MsgAction.NUDGE,
                sender=bot_email,
                target=sender_email,
                payload={}
            ))
        else:
            msg = "Zuuuuum! O meu monitor tremeu todo! (6)"
            color = "#008040"

        responses.append(Packet(
            action=MsgAction.RECV_MSG,
            sender=bot_email,
            target=sender_email,
            payload={"text": msg, "color": color, "font": "Segoe UI", "bold": True}
        ))
        return responses

    def handle_bot_game_move(self, board: List[str], bot_mark: str = "O") -> int:
        """Calculates a smart move for Tic-Tac-Toe."""
        # 1. Check if bot can win in 1 move
        for i in range(9):
            if board[i] == "":
                board[i] = bot_mark
                if self._check_win(board, bot_mark):
                    board[i] = ""
                    return i
                board[i] = ""

        # 2. Check if player can win in 1 move and block
        player_mark = "X" if bot_mark == "O" else "O"
        for i in range(9):
            if board[i] == "":
                board[i] = player_mark
                if self._check_win(board, player_mark):
                    board[i] = ""
                    return i
                board[i] = ""

        # 3. Take center if available
        if board[4] == "":
            return 4

        # 4. Take random available spot
        available = [i for i, v in enumerate(board) if v == ""]
        return random.choice(available) if available else -1

    def _check_win(self, b: List[str], mark: str) -> bool:
        lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        return any(b[x] == b[y] == b[z] == mark for x, y, z in lines)
