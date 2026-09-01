"""
MSN Messenger Tic-Tac-Toe (Jogo do Galo) Multi-player Mini-Game
Integrated directly into the MSN chat session.
"""
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtGui import QFont


class MSNTicTacToeDialog(QDialog):
    sig_make_move = pyqtSignal(str, int, str)  # target_email, cell_idx, mark

    def __init__(self, opponent_email: str, opponent_nick: str, session_id: str, is_my_turn: bool = True, my_mark: str = "X", parent=None):
        super().__init__(parent)
        self.opponent_email = opponent_email
        self.opponent_nick = opponent_nick
        self.session_id = session_id
        self.is_my_turn = is_my_turn
        self.my_mark = my_mark
        self.opp_mark = "O" if my_mark == "X" else "X"

        self.board: List[str] = [""] * 9
        self.game_over = False

        self.setWindowTitle(f"🎮 Jogo do Galo com {opponent_nick}")
        self.setFixedSize(360, 420)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header Title
        title_lbl = QLabel(f"<b>Jogo do Galo do MSN</b>")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #0072c6; font-size: 16px;")
        layout.addWidget(title_lbl)

        # Status / Turn Label
        self.status_lbl = QLabel()
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.status_lbl)

        # 3x3 Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        self.buttons: List[QPushButton] = []

        for i in range(9):
            btn = QPushButton("")
            btn.setFixedSize(90, 90)
            btn.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    border: 2px solid #a3c8e5;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #eaf5fc;
                    border-color: #3b99db;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self._on_cell_clicked(idx))
            grid_layout.addWidget(btn, i // 3, i % 3)
            self.buttons.append(btn)

        layout.addLayout(grid_layout)

        # Reset / Close Button bar
        btn_bar = QHBoxLayout()
        self.reset_btn = QPushButton("🔄 Reiniciar Jogo")
        self.reset_btn.clicked.connect(self._reset_board)
        btn_bar.addWidget(self.reset_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        btn_bar.addWidget(self.close_btn)

        layout.addLayout(btn_bar)
        self._update_turn_display()

    def _on_cell_clicked(self, idx: int):
        if self.game_over or not self.is_my_turn or self.board[idx] != "":
            return

        self._apply_move(idx, self.my_mark)
        self.sig_make_move.emit(self.opponent_email, idx, self.my_mark)
        self.is_my_turn = False
        self._update_turn_display()
        self._check_game_state()

    def receive_remote_move(self, idx: int, mark: str):
        if 0 <= idx < 9 and self.board[idx] == "":
            self._apply_move(idx, mark)
            self.is_my_turn = True
            self._update_turn_display()
            self._check_game_state()

    def _apply_move(self, idx: int, mark: str):
        self.board[idx] = mark
        btn = self.buttons[idx]
        btn.setText(mark)
        if mark == "X":
            btn.setStyleSheet("background: #ffebeb; color: #e74c3c; border: 2px solid #e74c3c; border-radius: 8px;")
        else:
            btn.setStyleSheet("background: #ebf5ff; color: #2980b9; border: 2px solid #2980b9; border-radius: 8px;")

    def _update_turn_display(self):
        if self.game_over:
            return
        if self.is_my_turn:
            self.status_lbl.setText(f"👉 A tua vez ({self.my_mark})")
            self.status_lbl.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold;")
        else:
            self.status_lbl.setText(f"⏳ Vez de {self.opponent_nick} ({self.opp_mark})...")
            self.status_lbl.setStyleSheet("color: #7f8c8d; font-size: 13px; font-weight: bold;")

    def _check_game_state(self):
        win_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_lines:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                winner = self.board[a]
                self.game_over = True
                if winner == self.my_mark:
                    self.status_lbl.setText("🎉 Parabéns! Venceste o jogo!")
                    self.status_lbl.setStyleSheet("color: #27ae60; font-size: 15px; font-weight: bold;")
                else:
                    self.status_lbl.setText(f"😢 {self.opponent_nick} venceu a partida!")
                    self.status_lbl.setStyleSheet("color: #e74c3c; font-size: 15px; font-weight: bold;")
                return

        if all(cell != "" for cell in self.board):
            self.game_over = True
            self.status_lbl.setText("🤝 Empate!")
            self.status_lbl.setStyleSheet("color: #f39c12; font-size: 15px; font-weight: bold;")

    def _reset_board(self):
        self.board = [""] * 9
        self.game_over = False
        for btn in self.buttons:
            btn.setText("")
            btn.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    border: 2px solid #a3c8e5;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #eaf5fc;
                    border-color: #3b99db;
                }
            """)
        self.is_my_turn = (self.my_mark == "X")
        self._update_turn_display()
