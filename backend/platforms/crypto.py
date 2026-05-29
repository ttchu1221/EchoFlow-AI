"""Cookie 加密存储"""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet

_KEY_FILE = Path(__file__).parent.parent / "data" / ".secret_key"


def _get_key() -> bytes:
    """获取或生成加密密钥（持久化到文件）"""
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()
    key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(key)
    # 限制权限
    os.chmod(_KEY_FILE, 0o600)
    return key


def encrypt_cookie(plain: str) -> str:
    """加密 Cookie 字符串 → base64 密文"""
    f = Fernet(_get_key())
    return f.encrypt(plain.encode()).decode()


def decrypt_cookie(encrypted: str) -> str:
    """解密 Cookie"""
    f = Fernet(_get_key())
    return f.decrypt(encrypted.encode()).decode()
