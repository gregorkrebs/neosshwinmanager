"""
Secure memory handling for NeoSSHWinManager.
Ensures passwords are never stored as plain strings in RAM longer than necessary.
"""

import ctypes
import gc
import os
import sys
from typing import Optional, Union


class SecureBytes:
    """
    A secure bytearray wrapper that ensures data is wiped from memory when no longer needed.
    Uses multiple overwrites (DoD 5220.22-M inspired) to prevent data recovery.
    """
    
    def __init__(self, data: Optional[Union[bytes, str, bytearray]] = None):
        self._data: Optional[bytearray] = None
        self._locked = False
        
        if data is not None:
            if isinstance(data, str):
                data = data.encode('utf-8')
            if isinstance(data, bytes):
                self._data = bytearray(data)
            elif isinstance(data, bytearray):
                self._data = data
            else:
                raise TypeError("Data must be bytes, str, or bytearray")
    
    def __len__(self) -> int:
        if self._data is None:
            return 0
        return len(self._data)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wipe()
        return False
    
    def __del__(self):
        # Attempt to wipe on garbage collection
        if not self._locked and self._data is not None:
            self.wipe()
    
    def wipe(self) -> None:
        """Securely wipe the data from memory by overwriting with zeros and random data."""
        if self._data is not None:
            # Multiple overwrites for security (DoD 5220.22-M inspired)
            patterns = [0x00, 0xFF, 0x00]  # Zero, ones, zero
            for pattern in patterns:
                for i in range(len(self._data)):
                    self._data[i] = pattern
            # Random overwrite
            for i in range(len(self._data)):
                self._data[i] = os.urandom(1)[0]
            # Final zero overwrite
            for i in range(len(self._data)):
                self._data[i] = 0
            self._data = None
            # Force garbage collection
            gc.collect()
    
    def get_bytes(self) -> Optional[bytes]:
        """Get the data as bytes (for use, not for long-term storage)."""
        if self._data is None:
            return None
        return bytes(self._data)
    
    def get_bytearray(self) -> Optional[bytearray]:
        """Get the data as bytearray (for modification)."""
        return self._data
    
    def decode(self, encoding: str = 'utf-8') -> Optional[str]:
        """Decode the bytes to a string."""
        if self._data is None:
            return None
        return self._data.decode(encoding)
    
    def append(self, data: Union[bytes, int]) -> None:
        """Append data to the secure buffer."""
        if self._data is None:
            if isinstance(data, int):
                self._data = bytearray([data])
            else:
                self._data = bytearray(data)
        else:
            if isinstance(data, int):
                self._data.append(data)
            else:
                self._data.extend(data)
    
    def lock(self) -> None:
        """Lock the buffer to prevent automatic wiping."""
        self._locked = True
    
    def unlock(self) -> None:
        """Unlock the buffer to allow wiping."""
        self._locked = False
    
    def is_empty(self) -> bool:
        """Check if the buffer is empty or wiped."""
        return self._data is None or len(self._data) == 0
    
    @classmethod
    def from_string(cls, s: str) -> 'SecureBytes':
        """Create a SecureBytes from a string."""
        return cls(s.encode('utf-8'))
    
    @classmethod
    def random(cls, length: int) -> 'SecureBytes':
        """Create a SecureBytes with cryptographically secure random data."""
        return cls(os.urandom(length))


def secure_wipe_bytes(data: Optional[bytearray]) -> None:
    """
    Securely wipe a bytearray by overwriting it with zeros and random data.
    
    Args:
        data: The bytearray to wipe
    """
    if data is None:
        return
    
    # Multiple overwrites for security
    patterns = [0x00, 0xFF, 0x00]  # Zero, ones, zero (DoD 5220.22-M inspired)
    
    for pattern in patterns:
        for i in range(len(data)):
            data[i] = pattern
    
    # Final random overwrite
    for i in range(len(data)):
        data[i] = os.urandom(1)[0]
    
    # Final zero
    for i in range(len(data)):
        data[i] = 0


def secure_wipe_string(s: Optional[str]) -> None:
    """
    Attempt to securely wipe a string from memory.
    Note: In Python, strings are immutable, so this is best-effort.
    
    Args:
        s: The string to wipe
    """
    if s is None:
        return
    
    # We can't truly wipe strings in Python due to immutability
    # and string interning, but we can help by removing references
    del s
    gc.collect()


def secure_compare(a: bytes, b: bytes) -> bool:
    """
    Constant-time comparison of two byte strings to prevent timing attacks.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0


def mlock_memory(data: bytearray) -> bool:
    """
    Attempt to lock memory to prevent swapping to disk.
    
    Args:
        data: The bytearray to lock
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == 'win32':
            # Windows: use VirtualLock
            kernel32 = ctypes.windll.kernel32
            return kernel32.VirtualLock(
                ctypes.c_char.from_buffer(data),
                ctypes.c_size_t(len(data))
            ) != 0
        else:
            # Unix-like: use mlock
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            return libc.mlock(
                ctypes.c_char.from_buffer(data),
                ctypes.c_size_t(len(data))
            ) == 0
    except Exception:
        return False


def munlock_memory(data: bytearray) -> bool:
    """
    Unlock previously locked memory.
    
    Args:
        data: The bytearray to unlock
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == 'win32':
            kernel32 = ctypes.windll.kernel32
            return kernel32.VirtualUnlock(
                ctypes.c_char.from_buffer(data),
                ctypes.c_size_t(len(data))
            ) != 0
        else:
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            return libc.munlock(
                ctypes.c_char.from_buffer(data),
                ctypes.c_size_t(len(data))
            ) == 0
    except Exception:
        return False
