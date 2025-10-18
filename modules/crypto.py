"""
Cryptographic functions for signing and verification using Ed25519
with deterministic device-bound keys
"""

import hashlib
import platform
import subprocess
import uuid
from typing import Tuple, Dict
from pathlib import Path

from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# Application-specific secret for key derivation (should be unique per app)
APP_SECRET = b"pixealed-v1-2025"


class DeviceKeyManager:
    """Manages device-specific signing keys with deterministic derivation"""
    
    def __init__(self):
        self.signing_key: bytes = None
        self.public_key: bytes = None
        self.device_fingerprint: str = None
        self.trust_level: str = None
        self.is_hardware_backed: bool = False
        self.device_id: str = None
    
    def get_device_info(self) -> Dict[str, str]:
        """Get device information including fingerprint and trust level"""
        return {
            "device_fingerprint": self.device_fingerprint or "",
            "trust_level": self.trust_level or "Unknown",
            "is_hardware_backed": str(self.is_hardware_backed),
            "device_id": self.device_id or ""
        }


def get_default_device_id() -> str:
    """
    Get a stable device identifier based on platform
    
    Priority order:
    1. Linux: /etc/machine-id
    2. Windows: MachineGuid from registry
    3. macOS: IOPlatformUUID
    4. Fallback: MAC address or CPU serial
    
    Returns:
        Stable device identifier as string
    """
    system = platform.system()
    
    try:
        if system == "Linux":
            # Try /etc/machine-id first
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                return machine_id_path.read_text().strip()
            
            # Fallback to dbus machine-id
            dbus_id_path = Path("/var/lib/dbus/machine-id")
            if dbus_id_path.exists():
                return dbus_id_path.read_text().strip()
        
        elif system == "Windows":
            # Get MachineGuid from registry
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography",
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                )
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                return machine_guid
            except Exception:
                pass
        
        elif system == "Darwin":  # macOS
            # Get IOPlatformUUID
            try:
                result = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        uuid_str = line.split('"')[3]
                        return uuid_str
            except Exception:
                pass
    
    except Exception:
        pass
    
    # Ultimate fallback: MAC address hash
    try:
        mac = uuid.getnode()
        return hashlib.sha256(str(mac).encode()).hexdigest()[:32]
    except Exception:
        # Last resort: random but persistent UUID (should be cached)
        return str(uuid.uuid4())


def _derive_deterministic_key(device_id: str) -> Tuple[bytes, bytes]:
    """
    Derive a deterministic Ed25519 key from device ID using HKDF
    
    Args:
        device_id: Stable device identifier
        
    Returns:
        Tuple of (signing_key, public_key) as raw bytes
    """
    # Use HKDF to derive a 32-byte seed from device_id + app_secret
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # Ed25519 seed length
        salt=APP_SECRET,
        info=b"pixealed-device-signing-key"
    )
    
    seed = hkdf.derive(device_id.encode())
    
    # Generate Ed25519 key from deterministic seed
    signing_key = SigningKey(seed)
    public_key = signing_key.verify_key
    
    return bytes(signing_key), bytes(public_key)


def _compute_device_fingerprint(public_key: bytes) -> str:
    """
    Compute SHA256 fingerprint of public key
    
    Args:
        public_key: Ed25519 public key (32 bytes)
        
    Returns:
        Hex-encoded SHA256 hash
    """
    return hashlib.sha256(public_key).hexdigest()


def load_or_generate_signing_key() -> DeviceKeyManager:
    """
    Load or generate a device-specific deterministic signing key
    
    Derives an Ed25519 key deterministically from the device ID,
    ensuring the same key is always generated on the same device.
    
    Returns:
        DeviceKeyManager with loaded keys and metadata
    """
    manager = DeviceKeyManager()
    
    # Get stable device identifier
    device_id = get_default_device_id()
    
    # Derive deterministic key from device ID
    signing_key, public_key = _derive_deterministic_key(device_id)
    
    # Populate manager
    manager.signing_key = signing_key
    manager.public_key = public_key
    manager.device_id = device_id
    manager.is_hardware_backed = False
    manager.trust_level = "Medium"
    
    # Compute device fingerprint
    manager.device_fingerprint = _compute_device_fingerprint(manager.public_key)
    
    return manager


def sign_manifest(manifest_bytes: bytes, signing_key: bytes) -> bytes:
    """
    Sign the manifest using Ed25519
    
    Args:
        manifest_bytes: Canonicalized manifest as bytes
        signing_key: Ed25519 signing key (32 bytes)
        
    Returns:
        Signature (64 bytes)
    """
    key = SigningKey(signing_key)
    signed = key.sign(manifest_bytes)
    
    # Return just the signature (without the message)
    return signed.signature


def verify_manifest(manifest_bytes: bytes, signature: bytes, public_key: bytes) -> bool:
    """
    Verify the manifest signature using Ed25519
    
    Args:
        manifest_bytes: Canonicalized manifest as bytes
        signature: Ed25519 signature (64 bytes)
        public_key: Ed25519 public key (32 bytes)
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        key = VerifyKey(public_key)
        key.verify(manifest_bytes, signature)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate a new Ed25519 keypair (random, not device-bound)
    
    Returns:
        Tuple of (signing_key, public_key) as raw bytes
    """
    signing_key = SigningKey.generate()
    public_key = signing_key.verify_key
    
    return bytes(signing_key), bytes(public_key)