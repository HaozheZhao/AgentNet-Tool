"""Encryption providers for file operations."""

from abc import ABC, abstractmethod
from typing import Union, Optional, Dict, Any
import json
import base64
import hashlib
import os


class EncryptionProvider(ABC):
    """Abstract base class for encryption providers."""
    
    @abstractmethod
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]]) -> bytes:
        """Encrypt data and return encrypted bytes."""
        pass
    
    @abstractmethod
    def decrypt_data(self, encrypted_data: bytes) -> Union[str, bytes, Dict[str, Any]]:
        """Decrypt data and return original format."""
        pass
    
    @abstractmethod
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Encrypt a file."""
        pass
    
    @abstractmethod
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Decrypt a file."""
        pass


class NoEncryption(EncryptionProvider):
    """Pass-through encryption provider (no actual encryption)."""
    
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]]) -> bytes:
        """Return data as bytes without encryption."""
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
        return data
    
    def decrypt_data(self, encrypted_data: bytes) -> Union[str, bytes, Dict[str, Any]]:
        """Return data without decryption."""
        try:
            # Try to decode as JSON first
            text = encrypted_data.decode('utf-8')
            return json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                # Try to decode as string
                return encrypted_data.decode('utf-8')
            except UnicodeDecodeError:
                # Return as bytes
                return encrypted_data
    
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Copy file without encryption."""
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            return True
        except Exception:
            return False
    
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Copy file without decryption."""
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            return True
        except Exception:
            return False


class SimpleEncryption(EncryptionProvider):
    """Simple XOR-based encryption (for demonstration - not secure)."""
    
    def __init__(self, key: Optional[str] = None):
        self.key = key or self._generate_key()
        self.key_bytes = self.key.encode('utf-8')
    
    def _generate_key(self) -> str:
        """Generate a simple key based on system info."""
        import platform
        import getpass
        
        system_info = f"{platform.node()}{getpass.getuser()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:32]
    
    def _xor_encrypt_decrypt(self, data: bytes) -> bytes:
        """XOR encrypt/decrypt data with key."""
        key_len = len(self.key_bytes)
        return bytes(data[i] ^ self.key_bytes[i % key_len] for i in range(len(data)))
    
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]]) -> bytes:
        """Encrypt data using XOR."""
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self._xor_encrypt_decrypt(data)
        # Prepend a simple header to identify encrypted data
        header = b"ENCRYPTED_V1:"
        return header + base64.b64encode(encrypted)
    
    def decrypt_data(self, encrypted_data: bytes) -> Union[str, bytes, Dict[str, Any]]:
        """Decrypt XOR-encrypted data."""
        try:
            header = b"ENCRYPTED_V1:"
            if not encrypted_data.startswith(header):
                # Not encrypted, return as-is
                return encrypted_data
            
            # Remove header and decode base64
            b64_data = encrypted_data[len(header):]
            encrypted_bytes = base64.b64decode(b64_data)
            
            # Decrypt
            decrypted = self._xor_encrypt_decrypt(encrypted_bytes)
            
            # Try to parse as JSON first
            try:
                text = decrypted.decode('utf-8')
                return json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                try:
                    return decrypted.decode('utf-8')
                except UnicodeDecodeError:
                    return decrypted
                    
        except Exception:
            # If decryption fails, return original data
            return encrypted_data
    
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Encrypt a file."""
        try:
            with open(input_path, 'rb') as infile:
                data = infile.read()
            
            encrypted_data = self.encrypt_data(data)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(encrypted_data)
            
            return True
        except Exception:
            return False
    
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Decrypt a file."""
        try:
            with open(input_path, 'rb') as infile:
                encrypted_data = infile.read()
            
            decrypted_data = self.decrypt_data(encrypted_data)
            
            if isinstance(decrypted_data, str):
                decrypted_data = decrypted_data.encode('utf-8')
            elif isinstance(decrypted_data, dict):
                decrypted_data = json.dumps(decrypted_data).encode('utf-8')
            
            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)
            
            return True
        except Exception:
            return False


class AESEncryption(EncryptionProvider):
    """AES-based encryption (requires cryptography library)."""
    
    def __init__(self, key: Optional[bytes] = None):
        try:
            from cryptography.fernet import Fernet
            self.fernet_available = True
            
            if key is None:
                # Generate key from system info
                import platform
                import getpass
                system_info = f"{platform.node()}{getpass.getuser()}"
                key_material = hashlib.sha256(system_info.encode()).digest()
                key = base64.urlsafe_b64encode(key_material)
            
            self.cipher = Fernet(key)
            
        except ImportError:
            self.fernet_available = False
            # Fall back to simple encryption
            self.fallback = SimpleEncryption()
    
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]]) -> bytes:
        """Encrypt data using AES."""
        if not self.fernet_available:
            return self.fallback.encrypt_data(data)
        
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> Union[str, bytes, Dict[str, Any]]:
        """Decrypt AES-encrypted data."""
        if not self.fernet_available:
            return self.fallback.decrypt_data(encrypted_data)
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data)
            
            # Try to parse as JSON first
            try:
                text = decrypted.decode('utf-8')
                return json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                try:
                    return decrypted.decode('utf-8')
                except UnicodeDecodeError:
                    return decrypted
                    
        except Exception:
            # If decryption fails, return original data
            return encrypted_data
    
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Encrypt a file using AES."""
        if not self.fernet_available:
            return self.fallback.encrypt_file(input_path, output_path)
        
        try:
            with open(input_path, 'rb') as infile:
                data = infile.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(encrypted_data)
            
            return True
        except Exception:
            return False
    
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Decrypt a file using AES."""
        if not self.fernet_available:
            return self.fallback.decrypt_file(input_path, output_path)
        
        try:
            with open(input_path, 'rb') as infile:
                encrypted_data = infile.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)
            
            return True
        except Exception:
            return False


def create_encryption_provider(provider_type: str = "simple", 
                             key: Optional[Union[str, bytes]] = None) -> EncryptionProvider:
    """Create an encryption provider."""
    if provider_type == "none":
        return NoEncryption()
    elif provider_type == "simple":
        return SimpleEncryption(key)
    elif provider_type == "aes":
        return AESEncryption(key)
    else:
        raise ValueError(f"Unknown encryption provider: {provider_type}")


# Utility functions for backward compatibility with original utils.py

def write_encrypted_json(file_path: str, data: Dict[str, Any], 
                        encryption_provider: Optional[EncryptionProvider] = None) -> None:
    """Write encrypted JSON data to file."""
    if encryption_provider is None:
        encryption_provider = create_encryption_provider("simple")
    
    encrypted_data = encryption_provider.encrypt_data(data)
    with open(file_path, 'wb') as f:
        f.write(encrypted_data)


def read_encrypted_json(file_path: str, 
                       encryption_provider: Optional[EncryptionProvider] = None) -> Dict[str, Any]:
    """Read encrypted JSON data from file."""
    if encryption_provider is None:
        encryption_provider = create_encryption_provider("simple")
    
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()
    
    decrypted_data = encryption_provider.decrypt_data(encrypted_data)
    
    if isinstance(decrypted_data, dict):
        return decrypted_data
    elif isinstance(decrypted_data, str):
        import json
        return json.loads(decrypted_data)
    else:
        raise ValueError("Decrypted data is not JSON format")


def write_encrypted_jsonl(file_path: str, data_list: list, 
                         encryption_provider: Optional[EncryptionProvider] = None) -> None:
    """Write encrypted JSONL data to file."""
    if encryption_provider is None:
        encryption_provider = create_encryption_provider("simple")
    
    lines = []
    for item in data_list:
        line = json.dumps(item) + '\n'
        lines.append(line)
    
    content = ''.join(lines)
    encrypted_data = encryption_provider.encrypt_data(content)
    
    with open(file_path, 'wb') as f:
        f.write(encrypted_data)


def read_encrypted_jsonl(file_path: str, 
                        encryption_provider: Optional[EncryptionProvider] = None) -> list:
    """Read encrypted JSONL data from file."""
    if encryption_provider is None:
        encryption_provider = create_encryption_provider("simple")
    
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()
    
    decrypted_data = encryption_provider.decrypt_data(encrypted_data)
    
    if isinstance(decrypted_data, bytes):
        decrypted_data = decrypted_data.decode('utf-8')
    
    lines = decrypted_data.strip().split('\n')
    result = []
    
    for line in lines:
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return result