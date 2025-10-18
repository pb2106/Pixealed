"""
Core conversion functions for .pxl format
"""

import struct
import json
from typing import Tuple, Dict, Any

from .metadata import extract_metadata
from .utils import chunk_bytes, canonical_json
from .merkle import build_merkle_tree
from .crypto import sign_manifest, verify_manifest

# Constants
MAGIC = b"PXL!"
FOOTER = b"END!"
VERSION = 0x01
CHUNK_SIZE = 256 * 1024  # 256 KB


def pack_image(input_file: str, output_file: str, signing_key: bytes) -> None:
    """
    Convert an image to .pxl format
    
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
    
    # Canonicalize and sign manifest
    manifest_json = canonical_json(manifest)
    manifest_bytes = manifest_json.encode("utf-8")
    signature = sign_manifest(manifest_bytes, signing_key)
    
    # Write .pxl file
    with open(output_file, "wb") as f:
        # MAGIC
        f.write(MAGIC)
        
        # VERSION
        f.write(struct.pack("B", VERSION))
        
        # IMAGE_CHUNKS
        f.write(image_bytes)
        
        # MANIFEST (length-prefixed)
        f.write(struct.pack("<I", len(manifest_bytes)))
        f.write(manifest_bytes)
        
        # SIGNATURE (64 bytes for Ed25519)
        f.write(signature)
        
        # FOOTER
        f.write(FOOTER)


def read_pxl(pxl_file: str) -> Tuple[bytes, Dict[str, Any]]:
    """
    Read a .pxl file and extract image bytes and metadata
    
    Args:
        pxl_file: Path to .pxl file
        
    Returns:
        Tuple of (image_bytes, metadata_dict)
    """
    with open(pxl_file, "rb") as f:
        # Read MAGIC
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError(f"Invalid .pxl file: wrong magic bytes")
        
        # Read VERSION
        version = struct.unpack("B", f.read(1))[0]
        if version != VERSION:
            raise ValueError(f"Unsupported .pxl version: {version}")
        
        # Read entire rest of file
        remaining = f.read()
    
    # Find FOOTER position (last 4 bytes should be FOOTER)
    if remaining[-4:] != FOOTER:
        raise ValueError("Invalid .pxl file: missing footer")
    
    # Remove footer
    remaining = remaining[:-4]
    
    # Signature is last 64 bytes before footer
    signature = remaining[-64:]
    remaining = remaining[:-64]
    
    # Manifest length is last 4 bytes before signature
    manifest_len = struct.unpack("<I", remaining[-4:])[0]
    remaining = remaining[:-4]
    
    # Extract manifest
    manifest_bytes = remaining[-manifest_len:]
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    
    # Extract image bytes (everything before manifest)
    image_bytes = remaining[:-manifest_len]
    
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
            # Read MAGIC
            magic = f.read(4)
            if magic != MAGIC:
                return False
            
            # Read VERSION
            version = struct.unpack("B", f.read(1))[0]
            if version != VERSION:
                return False
            
            # Read rest
            remaining = f.read()
        
        # Validate footer
        if remaining[-4:] != FOOTER:
            return False
        
        remaining = remaining[:-4]
        
        # Extract signature
        signature = remaining[-64:]
        remaining = remaining[:-64]
        
        # Extract manifest
        manifest_len = struct.unpack("<I", remaining[-4:])[0]
        remaining = remaining[:-4]
        manifest_bytes = remaining[-manifest_len:]
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        
        # Extract image bytes
        image_bytes = remaining[:-manifest_len]
        
        # Verify signature
        if not verify_manifest(manifest_bytes, signature, public_key):
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