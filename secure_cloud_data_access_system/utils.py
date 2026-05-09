from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

import bcrypt
from cryptography.fernet import Fernet
from flask import current_app, request
from werkzeug.utils import secure_filename

from .database.extensions import db
from .models import AccessLog


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        key = Fernet.generate_key().decode("utf-8")
        os.environ["FERNET_KEY"] = key
    return Fernet(key.encode("utf-8"))


def encrypt_pattern(pattern: str) -> str:
    return _get_fernet().encrypt(pattern.encode("utf-8")).decode("utf-8")


def decrypt_pattern(pattern: str) -> str:
    return _get_fernet().decrypt(pattern.encode("utf-8")).decode("utf-8")


def make_reset_token() -> Tuple[str, datetime]:
    return secrets.token_urlsafe(32), datetime.utcnow() + timedelta(minutes=20)


def allowed_filename(filename: str) -> str:
    token = secrets.token_hex(8)
    return f"{token}_{secure_filename(filename)}"


def log_access(
    user_id: int,
    action: str,
    status: str,
    file_id: Optional[int] = None,
    details: Optional[str] = None,
):
    entry = AccessLog(
        user_id=user_id,
        file_id=file_id,
        action=action,
        status=status,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=(request.user_agent.string or "")[:255],
        details=details,
    )
    db.session.add(entry)
    db.session.commit()


def current_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
