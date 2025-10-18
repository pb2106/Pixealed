"""
Pixealed - Decentralized Tamper-Proof Image Format (.pxl)

A self-contained, tamper-evident image file format that stores original image data,
camera-generated metadata, and ensures integrity using chunk hashes, Merkle trees,
and digital signatures.
"""

from .converter import pack_image, read_pxl, verify_pxl
from .crypto import generate_keypair, sign_manifest, verify_manifest
from .merkle import hash_chunk, build_merkle_tree, verify_chunk
from .metadata import extract_metadata, generate_synthetic_metadata
from .utils import chunk_bytes, canonical_json

__version__ = "0.1.0"
__all__ = [
    # Main API
    "pack_image",
    "read_pxl",
    "verify_pxl",
    "generate_keypair",
    # Crypto utilities
    "sign_manifest",
    "verify_manifest",
    # Merkle tree utilities
    "hash_chunk",
    "build_merkle_tree",
    "verify_chunk",
    # Metadata utilities
    "extract_metadata",
    "generate_synthetic_metadata",
    # Helper utilities
    "chunk_bytes",
    "canonical_json",
]