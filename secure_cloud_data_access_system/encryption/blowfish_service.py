import base64
import hashlib
import os
import time
from pathlib import Path

from Crypto.Cipher import Blowfish
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class OptimizedBlowfishService:
    def __init__(self) -> None:
        secret = os.getenv("BLOWFISH_SECRET", "change-this-blowfish-secret")
        self.key = hashlib.sha256(secret.encode("utf-8")).digest()[:56]
        self.block_size = Blowfish.block_size

    def encrypt_file(self, source_path: str, destination_path: str) -> dict:
        iv = get_random_bytes(self.block_size)
        cipher = Blowfish.new(self.key, Blowfish.MODE_CBC, iv)
        started = time.perf_counter()

        with open(source_path, "rb") as src:
            payload = src.read()

        encrypted = cipher.encrypt(pad(payload, self.block_size))
        with open(destination_path, "wb") as dst:
            dst.write(iv + encrypted)

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "encrypted",
            "duration_ms": elapsed_ms,
            "input_size": len(payload),
            "output_size": len(encrypted) + len(iv),
            "key_fingerprint": base64.urlsafe_b64encode(self.key[:12]).decode("utf-8"),
        }

    def decrypt_file(self, source_path: str, destination_path: str) -> dict:
        started = time.perf_counter()

        with open(source_path, "rb") as src:
            payload = src.read()

        iv = payload[: self.block_size]
        encrypted = payload[self.block_size :]
        cipher = Blowfish.new(self.key, Blowfish.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), self.block_size)

        with open(destination_path, "wb") as dst:
            dst.write(decrypted)

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "decrypted",
            "duration_ms": elapsed_ms,
            "output_size": len(decrypted),
        }


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    mapping = {
        ".pdf": "PDF",
        ".docx": "DOCX",
        ".png": "Image",
        ".jpg": "Image",
        ".jpeg": "Image",
        ".gif": "Image",
        ".zip": "ZIP",
        ".txt": "Text",
    }
    return mapping.get(suffix, "Other")
