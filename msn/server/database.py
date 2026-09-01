"""
MSN Messenger Database Manager (SQLite)
Handles persistent storage for users, passwords, avatars, personal messages, and contact lists.
"""
import contextlib
import hashlib
import sqlite3
import os
import time
from typing import Dict, List, Optional, Tuple
from msn.common.protocol import UserProfile, UserStatus


class MSNDatabase:
    def __init__(self, db_path: str = "msn_data.db"):
        self.db_path = db_path
        self._init_db()

    @contextlib.contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _hash_password(self, password: str, salt: str = "msn_salt_live_2026") -> str:
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    avatar_id TEXT DEFAULT 'avatar_1',
                    personal_msg TEXT DEFAULT '',
                    created_at REAL NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    user_email TEXT NOT NULL,
                    contact_email TEXT NOT NULL,
                    custom_group TEXT DEFAULT 'Amigos',
                    created_at REAL NOT NULL,
                    PRIMARY KEY (user_email, contact_email)
                )
            """)
            conn.commit()

    def register_user(self, email: str, password: str, nickname: str, avatar_id: str = "avatar_1", personal_msg: str = "") -> Tuple[bool, str]:
        email = email.strip().lower()
        if not email or "@" not in email:
            return False, "Endereço de email inválido."

        if not password or len(password) < 4:
            return False, "A palavra-passe deve ter pelo menos 4 caracteres."

        if not nickname:
            nickname = email.split("@")[0]

        pw_hash = self._hash_password(password)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, password_hash, nickname, avatar_id, personal_msg, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (email, pw_hash, nickname, avatar_id, personal_msg, time.time())
                )
                conn.commit()
                return True, "Conta criada com sucesso!"
        except sqlite3.IntegrityError:
            return False, "Já existe uma conta registada com este endereço de email."
        except Exception as e:
            return False, f"Erro ao registar conta: {str(e)}"

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[UserProfile], str]:
        email = email.strip().lower()
        pw_hash = self._hash_password(password)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                if not row:
                    return False, None, "Utilizador não encontrado. Verifique o email ou registe uma nova conta."

                if row["password_hash"] != pw_hash:
                    return False, None, "Palavra-passe incorreta."

                profile = UserProfile(
                    email=row["email"],
                    nickname=row["nickname"],
                    avatar_id=row["avatar_id"] or "avatar_1",
                    personal_msg=row["personal_msg"] or "",
                    status=UserStatus.ONLINE
                )
                return True, profile, "Autenticação bem-sucedida."
        except Exception as e:
            return False, None, f"Erro na autenticação: {str(e)}"

    def reset_password(self, email: str, new_password: str) -> Tuple[bool, str]:
        email = email.strip().lower()
        if not new_password or len(new_password) < 4:
            return False, "A nova palavra-passe deve ter pelo menos 4 caracteres."

        pw_hash = self._hash_password(new_password)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
                if not cursor.fetchone():
                    # Create account if it doesn't exist
                    cursor.execute(
                        "INSERT INTO users (email, password_hash, nickname, avatar_id, personal_msg, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (email, pw_hash, email.split("@")[0], "avatar_1", "", time.time())
                    )
                else:
                    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (pw_hash, email))
                conn.commit()
                return True, "Palavra-passe atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar palavra-passe: {str(e)}"

    def update_user_profile(self, email: str, nickname: Optional[str] = None, avatar_id: Optional[str] = None, personal_msg: Optional[str] = None):
        email = email.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if nickname is not None:
                cursor.execute("UPDATE users SET nickname = ? WHERE email = ?", (nickname, email))
            if avatar_id is not None:
                cursor.execute("UPDATE users SET avatar_id = ? WHERE email = ?", (avatar_id, email))
            if personal_msg is not None:
                cursor.execute("UPDATE users SET personal_msg = ? WHERE email = ?", (personal_msg, email))
            conn.commit()

    def get_user_profile(self, email: str) -> Optional[UserProfile]:
        email = email.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return UserProfile(
                    email=row["email"],
                    nickname=row["nickname"],
                    avatar_id=row["avatar_id"] or "avatar_1",
                    personal_msg=row["personal_msg"] or "",
                    status=UserStatus.OFFLINE
                )
        return None

    def add_contact(self, user_email: str, contact_email: str, group: str = "Amigos") -> bool:
        user_email = user_email.strip().lower()
        contact_email = contact_email.strip().lower()

        if user_email == contact_email:
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO contacts (user_email, contact_email, custom_group, created_at) VALUES (?, ?, ?, ?)",
                    (user_email, contact_email, group, time.time())
                )
                conn.commit()
                return True
        except Exception:
            return False

    def remove_contact(self, user_email: str, contact_email: str) -> bool:
        user_email = user_email.strip().lower()
        contact_email = contact_email.strip().lower()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE user_email = ? AND contact_email = ?", (user_email, contact_email))
                conn.commit()
                return True
        except Exception:
            return False

    def get_contacts_for_user(self, user_email: str) -> List[UserProfile]:
        user_email = user_email.strip().lower()
        contacts = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.contact_email, c.custom_group, u.nickname, u.avatar_id, u.personal_msg 
                FROM contacts c 
                LEFT JOIN users u ON c.contact_email = u.email 
                WHERE c.user_email = ?
            """, (user_email,))
            rows = cursor.fetchall()
            for r in rows:
                c_email = r["contact_email"]
                nickname = r["nickname"] or c_email.split("@")[0]
                avatar_id = r["avatar_id"] or "avatar_1"
                personal_msg = r["personal_msg"] or ""
                group = r["custom_group"] or "Amigos"

                contacts.append(UserProfile(
                    email=c_email,
                    nickname=nickname,
                    avatar_id=avatar_id,
                    personal_msg=personal_msg,
                    group=group,
                    status=UserStatus.OFFLINE
                ))
        return contacts
