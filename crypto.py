"""
Cryptographic functions for signing and verification using Ed25519
"""

from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from typing import Tuple


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate a new Ed25519 keypair
    
    Returns:
        Tuple of (signing_key, public_key) as raw bytes
    """
    signing_key = SigningKey.generate()
    public_key = signing_key.verify_key
    
    return bytes(signing_key), bytes(public_key)


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
    except Exception as e:
        print(f"Verification exception: {e}")
        return False