"""
Security tests for NeoSSHWinManager.
Tests for:
1. Command injection prevention
2. Password encryption/decryption
3. Secure memory handling
4. Key derivation (PBKDF2 and Argon2)
5. Input validation
"""

import sys
import os
import tempfile
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.secure_memory import SecureBytes, secure_wipe_bytes, secure_compare
from src.ssh_launcher import _is_safe_ssh_identifier, _is_safe_file_path

# Import crypto functions from crypto.py
try:
    from src.crypto import (
        derive_key_argon2,
        derive_key_pbkdf2_secure,
        store_key_in_credential_manager,
        retrieve_key_from_credential_manager,
        is_keyring_available,
        encrypt,
        decrypt,
        generate_enc_key,
        SecureCrypto,
        KeyManager,
        generate_secure_random,
    )
    _CRYPTO_AVAILABLE = True
except ImportError as e:
    _CRYPTO_AVAILABLE = False
    print(f"Crypto import error: {e}")


class TestCommandInjectionPrevention:
    """Tests for command injection vulnerabilities."""
    
    def test_safe_hostname_valid(self):
        """Test that valid hostnames are accepted."""
        assert _is_safe_ssh_identifier("example.com") is True
        assert _is_safe_ssh_identifier("192.168.1.1") is True
        assert _is_safe_ssh_identifier("server-01") is True
        assert _is_safe_ssh_identifier("user@host") is True
    
    def test_safe_hostname_invalid_with_semicolon(self):
        """Test that hostnames with semicolon are rejected (command injection)."""
        assert _is_safe_ssh_identifier("example.com; rm -rf /") is False
        assert _is_safe_ssh_identifier("host;whoami") is False
    
    def test_safe_hostname_invalid_with_pipe(self):
        """Test that hostnames with pipe are rejected."""
        assert _is_safe_ssh_identifier("example.com | cat /etc/passwd") is False
    
    def test_safe_hostname_invalid_with_backticks(self):
        """Test that hostnames with backticks are rejected."""
        assert _is_safe_ssh_identifier("host`whoami`") is False
    
    def test_safe_hostname_invalid_with_dollar(self):
        """Test that hostnames with dollar sign are rejected."""
        assert _is_safe_ssh_identifier("host$USER") is False
    
    def test_safe_hostname_invalid_with_ampersand(self):
        """Test that hostnames with ampersand are rejected."""
        assert _is_safe_ssh_identifier("host && whoami") is False
    
    def test_safe_file_path_traversal(self):
        """Test that path traversal is rejected."""
        assert _is_safe_file_path("../../../etc/passwd") is False
        assert _is_safe_file_path("..\\windows\\system32") is False
    
    def test_safe_file_path_valid(self):
        """Test that valid file paths are accepted."""
        assert _is_safe_file_path("C:\\Users\\test\\key.pem") is True
        assert _is_safe_file_path("/home/user/.ssh/id_rsa") is True
    
    def test_safe_file_path_with_shell_chars(self):
        """Test that paths with shell metacharacters are rejected."""
        assert _is_safe_file_path("/path;rm -rf /") is False
        assert _is_safe_file_path("/path|cat /etc/passwd") is False


class TestSecureMemory:
    """Tests for secure memory handling."""
    
    def test_secure_bytes_creation(self):
        """Test SecureBytes can be created from strings and bytes."""
        sb1 = SecureBytes.from_string("test password")
        assert len(sb1) == 13
        
        sb2 = SecureBytes(b"test bytes")
        assert len(sb2) == 10
    
    def test_secure_bytes_wipe(self):
        """Test that SecureBytes wipes data properly."""
        sb = SecureBytes(b"secret123")
        assert not sb.is_empty()
        sb.wipe()
        assert sb.is_empty()
        assert sb._data is None
    
    def test_secure_bytes_context_manager(self):
        """Test SecureBytes works as context manager."""
        with SecureBytes(b"secret") as sb:
            assert not sb.is_empty()
        # After exiting context, should be wiped
        assert sb.is_empty()
    
    def test_secure_bytes_get_bytes(self):
        """Test getting bytes from SecureBytes."""
        sb = SecureBytes(b"test")
        result = sb.get_bytes()
        assert result == b"test"
    
    def test_secure_bytes_decode(self):
        """Test decoding SecureBytes to string."""
        sb = SecureBytes.from_string("hello")
        result = sb.decode()
        assert result == "hello"


class TestCryptoFunctions:
    """Tests for cryptographic functions."""
    
    def test_generate_secure_random(self):
        """Test secure random generation."""
        r1 = generate_secure_random(32)
        r2 = generate_secure_random(32)
        assert len(r1) == 32
        assert len(r2) == 32
        assert r1 != r2  # Should be different each time
    
    def test_secure_compare_equal(self):
        """Test constant-time comparison with equal bytes."""
        a = b"test123"
        b = b"test123"
        assert secure_compare(a, b) is True
    
    def test_secure_compare_unequal(self):
        """Test constant-time comparison with unequal bytes."""
        a = b"test123"
        b = b"test456"
        assert secure_compare(a, b) is False
    
    def test_secure_compare_different_length(self):
        """Test constant-time comparison with different length."""
        a = b"short"
        b = b"longer string"
        assert secure_compare(a, b) is False
    
    def test_key_manager_derive_pbkdf2(self):
        """Test PBKDF2 key derivation."""
        km = KeyManager()
        password = SecureBytes.from_string("master_password_123")
        
        key, salt = km.initialize_with_password(password, use_argon2=False)
        
        assert len(key) == 32  # 256 bits
        assert len(salt) == 32  # 256 bits
        assert key is not None
        
        password.wipe()
    
    def test_key_manager_verify_correct_password(self):
        """Test password verification with correct password."""
        km = KeyManager()
        password = SecureBytes.from_string("correct_password")
        
        key, salt = km.initialize_with_password(password, use_argon2=False)
        
        # Verify with same password
        verify_pw = SecureBytes.from_string("correct_password")
        assert km.verify_password(verify_pw, salt, use_argon2=False) is True
        
        password.wipe()
        verify_pw.wipe()
    
    def test_key_manager_verify_wrong_password(self):
        """Test password verification with wrong password."""
        km = KeyManager()
        password = SecureBytes.from_string("correct_password")
        
        key, salt = km.initialize_with_password(password, use_argon2=False)
        
        # Verify with wrong password
        wrong_pw = SecureBytes.from_string("wrong_password")
        assert km.verify_password(wrong_pw, salt, use_argon2=False) is False
        
        password.wipe()
        wrong_pw.wipe()
    
    def test_key_manager_derive_connection_key(self):
        """Test deriving unique keys per connection."""
        km = KeyManager()
        password = SecureBytes.from_string("master_password")
        
        km.initialize_with_password(password, use_argon2=False)
        
        key1 = km.derive_connection_key("conn_001")
        key2 = km.derive_connection_key("conn_002")
        key3 = km.derive_connection_key("conn_001")  # Same as key1
        
        # Different connections should have different keys
        assert key1 != key2
        # Same connection should derive same key
        assert key1 == key3
        
        password.wipe()
    
    def test_encrypt_decrypt_data(self):
        """Test encryption and decryption with unique IV."""
        km = KeyManager()
        password = SecureBytes.from_string("master_password")
        
        key, salt = km.initialize_with_password(password, use_argon2=False)
        
        # Encrypt data
        plaintext = SecureBytes.from_string("sensitive data here")
        encrypted = SecureCrypto.encrypt_data(plaintext, key)
        
        # Encrypted should include IV (12 bytes) + ciphertext
        assert len(encrypted) > 12
        
        # Decrypt data
        decrypted = SecureCrypto.decrypt_data(encrypted, key)
        assert decrypted.decode() == "sensitive data here"
        
        password.wipe()
        plaintext.wipe()
        decrypted.wipe()
    
    def test_encrypt_unique_iv_per_encryption(self):
        """Test that each encryption produces unique IV and ciphertext."""
        km = KeyManager()
        password = SecureBytes.from_string("master_password")
        
        key, salt = km.initialize_with_password(password, use_argon2=False)
        
        # Encrypt same data twice
        plaintext = SecureBytes.from_string("same data")
        encrypted1 = SecureCrypto.encrypt_data(plaintext, key)
        encrypted2 = SecureCrypto.encrypt_data(plaintext, key)
        
        # Should be different (due to unique IV)
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        decrypted1 = SecureCrypto.decrypt_data(encrypted1, key)
        decrypted2 = SecureCrypto.decrypt_data(encrypted2, key)
        assert decrypted1.decode() == decrypted2.decode()
        
        password.wipe()
        plaintext.wipe()
        decrypted1.wipe()
        decrypted2.wipe()


class TestDatabaseSecurity:
    """Tests for database security."""
    
    def test_database_path_secure(self):
        """Test that database is created in secure location."""
        from src.database import get_db_path
        db_path = get_db_path()
        
        # Should be in APPDATA or home directory
        appdata = os.environ.get("APPDATA", str(os.path.expanduser("~")))
        assert str(db_path).startswith(appdata) or str(db_path).startswith(os.path.expanduser("~"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
