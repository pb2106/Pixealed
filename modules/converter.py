"""
Core conversion functions for .pxl format (Encrypted Non-Viewable Version)

.pxl files are encrypted and not viewable without decryption.
Structure: [ENCRYPTED_IMAGE][MAGIC][VERSION][MANIFEST_LEN][MANIFEST][SIGNATURE][NONCE_LEN][NONCE][FOOTER]
"""

import struct
import json
import os
from typing import Tuple, Dict, Any
import blake3
from nacl.bindings import (
    crypto_aead_xchacha20poly1305_ietf_encrypt,
    crypto_aead_xchacha20poly1305_ietf_decrypt
)

from .metadata import extract_metadata
from .utils import chunk_bytes, canonical_json
from .merkle import build_merkle_tree
from .crypto import sign_manifest, verify_manifest

# Constants
MAGIC = b"PXL!"
FOOTER = b"END!"
VERSION = 0x01
CHUNK_SIZE = 256 * 1024  # 256 KB
NONCE_SIZE = 24  # XChaCha20-Poly1305 nonce size


def pack_image(input_file: str, output_file: str, signing_key: bytes) -> None:
    """
    Convert an image to .pxl format (encrypted)
    
    The .pxl file is encrypted and not directly viewable.
    
    Args:
        input_file: Path to input image file
        output_file: Path to output .pxl file
        signing_key: Ed25519 signing key (32 bytes)
    """
    # Read image bytes
    with open(input_file, "rb") as f:
        image_bytes = f.read()
    
    # Extract metadata
    metadata = extract_metadata(input_file)
    
    # Split into chunks
    chunks = chunk_bytes(image_bytes, CHUNK_SIZE)
    
    # Build Merkle tree and get chunk hashes
    merkle_root, chunk_hashes = build_merkle_tree(chunks)
    
    # Build manifest
    manifest = {
        "metadata": metadata,
        "chunk_hashes": chunk_hashes,
        "merkle_root": merkle_root,
        "chunk_size": CHUNK_SIZE,
        "total_size": len(image_bytes),
        "num_chunks": len(chunks)
    }
    
    # Canonicalize manifest
    manifest_json = canonical_json(manifest)
    manifest_bytes = manifest_json.encode("utf-8")
    
    # Derive encryption key from manifest
    hasher = blake3.blake3(manifest_bytes)
    hasher.update(b"pxl-aead-key")
    key = hasher.digest(length=32)
    
    # Generate random nonce
    nonce = os.urandom(NONCE_SIZE)
    
    # Encrypt image bytes
    encrypted_image = crypto_aead_xchacha20poly1305_ietf_encrypt(
        image_bytes,
        b"",
        nonce,
        key
    )
    
    # Sign manifest
    signature = sign_manifest(manifest_bytes, signing_key)
    
    # Write .pxl file
    with open(output_file, "wb") as f:
        # ENCRYPTED_IMAGE_BYTES
        f.write(encrypted_image)
        
        # MAGIC
        f.write(MAGIC)
        
        # VERSION
        f.write(struct.pack("B", VERSION))
        
        # MANIFEST (length-prefixed)
        f.write(struct.pack("<I", len(manifest_bytes)))
        f.write(manifest_bytes)
        
        # SIGNATURE (64 bytes for Ed25519)
        f.write(signature)
        
        # NONCE (length-prefixed)
        f.write(struct.pack("B", len(nonce)))
        f.write(nonce)
        
        # FOOTER
        f.write(FOOTER)


def read_pxl(pxl_file: str) -> Tuple[bytes, Dict[str, Any]]:
    """
    Read a .pxl file and extract decrypted image bytes and metadata
    
    Args:
        pxl_file: Path to .pxl file
        
    Returns:
        Tuple of (image_bytes, metadata_dict)
    """
    with open(pxl_file, "rb") as f:
        all_data = f.read()
    
    # Find MAGIC position
    magic_pos = all_data.rfind(MAGIC)
    
    if magic_pos == -1:
        raise ValueError(f"Invalid .pxl file: MAGIC bytes not found")
    
    # Split data
    encrypted_image = all_data[:magic_pos]
    auth_block = all_data[magic_pos:]
    
    # Parse authenticity block
    offset = 0
    
    # MAGIC (4 bytes)
    magic = auth_block[offset:offset+4]
    if magic != MAGIC:
        raise ValueError(f"Invalid .pxl file: wrong magic bytes")
    offset += 4
    
    # VERSION (1 byte)
    version = struct.unpack("B", auth_block[offset:offset+1])[0]
    if version != VERSION:
        raise ValueError(f"Unsupported .pxl version: {version}")
    offset += 1
    
    # MANIFEST_LEN (4 bytes)
    manifest_len = struct.unpack("<I", auth_block[offset:offset+4])[0]
    offset += 4
    
    # MANIFEST
    manifest_bytes = auth_block[offset:offset+manifest_len]
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    offset += manifest_len
    
    # SIGNATURE (64 bytes)
    signature = auth_block[offset:offset+64]
    offset += 64
    
    # NONCE_LEN (1 byte)
    nonce_len = struct.unpack("B", auth_block[offset:offset+1])[0]
    offset += 1
    
    # NONCE
    nonce = auth_block[offset:offset+nonce_len]
    offset += nonce_len
    
    # FOOTER (4 bytes)
    footer = auth_block[offset:offset+4]
    if footer != FOOTER:
        raise ValueError("Invalid .pxl file: missing footer")
    
    # Derive decryption key from manifest
    hasher = blake3.blake3(manifest_bytes)
    hasher.update(b"pxl-aead-key")
    key = hasher.digest(length=32)
    
    # Decrypt image
    try:
        image_bytes = crypto_aead_xchacha20poly1305_ietf_decrypt(
            encrypted_image,
            b"",
            nonce,
            key
        )
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
    
    return image_bytes, manifest


def verify_pxl(pxl_file: str, public_key: bytes) -> bool:
    """
    Verify the integrity and authenticity of a .pxl file
    
    Args:
        pxl_file: Path to .pxl file
        public_key: Ed25519 public key (32 bytes)
        
    Returns:
        True if verification passes, False otherwise
    """
    try:
        with open(pxl_file, "rb") as f:
            all_data = f.read()
        
        # Find MAGIC position
        magic_pos = all_data.rfind(MAGIC)
        
        if magic_pos == -1:
            return False
        
        # Split data
        encrypted_image = all_data[:magic_pos]
        auth_block = all_data[magic_pos:]
        
        # Parse authenticity block
        offset = 0
        
        # MAGIC
        magic = auth_block[offset:offset+4]
        if magic != MAGIC:
            return False
        offset += 4
        
        # VERSION
        version = struct.unpack("B", auth_block[offset:offset+1])[0]
        if version != VERSION:
            return False
        offset += 1
        
        # MANIFEST_LEN
        manifest_len = struct.unpack("<I", auth_block[offset:offset+4])[0]
        offset += 4
        
        # MANIFEST
        manifest_bytes = auth_block[offset:offset+manifest_len]
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        offset += manifest_len
        
        # SIGNATURE
        signature = auth_block[offset:offset+64]
        offset += 64
        
        # NONCE_LEN
        nonce_len = struct.unpack("B", auth_block[offset:offset+1])[0]
        offset += 1
        
        # NONCE
        nonce = auth_block[offset:offset+nonce_len]
        offset += nonce_len
        
        # FOOTER
        footer = auth_block[offset:offset+4]
        if footer != FOOTER:
            return False
        
        # Verify signature
        if not verify_manifest(manifest_bytes, signature, public_key):
            return False
        
        # Derive decryption key from manifest
        hasher = blake3.blake3(manifest_bytes)
        hasher.update(b"pxl-aead-key")
        key = hasher.digest(length=32)
        
        # Attempt decryption
        try:
            image_bytes = crypto_aead_xchacha20poly1305_ietf_decrypt(
                encrypted_image,
                b"",
                nonce,
                key
            )
        except:
            return False
        
        # Verify chunk hashes
        chunks = chunk_bytes(image_bytes, manifest["chunk_size"])
        merkle_root, chunk_hashes = build_merkle_tree(chunks)
        
        # Compare hashes
        if chunk_hashes != manifest["chunk_hashes"]:
            return False
        
        if merkle_root != manifest["merkle_root"]:
            return False
        
        return True
        
    except Exception as e:
        print(f"Verification error: {e}")
        return False