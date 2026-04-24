# crypto.py – Kryptographie-Hilfsfunktionen für NEO SSH-Win Manager.
#
# Passwort-Hashing:  PBKDF2-HMAC-SHA256 (600.000 Iterationen, OWASP 2024)
# SSH-Passwortverschlüsselung: AES-256-GCM
#   - Jeder Benutzer hat einen zufälligen 256-bit Encryption Key
#   - Dieser Key wird mit dem abgeleiteten Benutzer-Passwort verschlüsselt
#   - SSH-Passwörter werden mit diesem Key verschlüsselt
#   - Wenn der Benutzer sein App-Passwort ändert, wird nur der Key re-encrypted
#
# pip install cryptography

import os
import secrets
import hashlib
import hmac
from typing import Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


# PBKDF2-Parameter (OWASP 2024 Empfehlung)
_PBKDF2_ITERATIONS = 600_000
_PBKDF2_HASH = "sha256"
_KEY_LEN = 32  # 256 bit


# ------------------------------------------------------------------
# Passwort-Hashing (für App-Login)
# ------------------------------------------------------------------

def hash_password(password: str) -> Tuple[str, str]:
    """
    Erzeugt einen sicheren Hash des App-Passworts.
    Returns (hash_hex, salt_hex).
    """
    salt = secrets.token_bytes(32)
    pw_hash = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LEN,
    )
    return pw_hash.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Prüft ob ein Passwort mit dem gespeicherten Hash übereinstimmt."""
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    actual = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LEN,
    )
    # Timing-safe Vergleich
    return hmac.compare_digest(actual, expected)


def derive_key(password: str, salt_hex: str) -> bytes:
    """
    Leitet einen 256-bit Schlüssel aus dem Passwort ab.
    Wird genutzt um den Encryption Key des Benutzers zu ver-/entschlüsseln.
    """
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LEN,
    )


# ------------------------------------------------------------------
# AES-256-GCM Verschlüsselung (für SSH-Passwörter und Encryption Key)
# ------------------------------------------------------------------

def generate_enc_key() -> bytes:
    """Erzeugt einen neuen zufälligen 256-bit Encryption Key."""
    return secrets.token_bytes(32)


def encrypt(plaintext: str, key: bytes) -> Tuple[str, str]:
    """
    Verschlüsselt einen String mit AES-256-GCM.
    Returns (ciphertext_hex, iv_hex).
    """
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError(
            "cryptography nicht installiert. "
            "Bitte ausführen: pip install cryptography"
        )
    iv = secrets.token_bytes(12)  # 96-bit IV für GCM
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return ct.hex(), iv.hex()


def decrypt(ciphertext_hex: str, iv_hex: str, key: bytes) -> str:
    """
    Entschlüsselt AES-256-GCM Ciphertext.
    Raises ValueError bei falschem Key (Authentication Tag schlägt fehl).
    """
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography nicht installiert.")
    ct = bytes.fromhex(ciphertext_hex)
    iv = bytes.fromhex(iv_hex)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ct, None).decode("utf-8")


def encrypt_key(enc_key: bytes, password: str, salt_hex: str) -> Tuple[str, str]:
    """Verschlüsselt den Encryption Key mit dem abgeleiteten Passwort-Key."""
    derived = derive_key(password, salt_hex)
    return encrypt(enc_key.hex(), derived)


def decrypt_key(enc_key_hex: str, iv_hex: str, password: str, salt_hex: str) -> bytes:
    """Entschlüsselt den Encryption Key mit dem abgeleiteten Passwort-Key."""
    derived = derive_key(password, salt_hex)
    key_hex = decrypt(enc_key_hex, iv_hex, derived)
    return bytes.fromhex(key_hex)


def is_available() -> bool:
    return _CRYPTO_AVAILABLE
