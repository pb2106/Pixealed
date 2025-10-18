"""
Pixealed - Decentralized Tamper-Proof Image Format (.pxl)

A self-contained, tamper-evident image file format that stores original image data,
camera-generated metadata, and ensures integrity using chunk hashes, Merkle trees,
and digital signatures.
"""

from .converter import pack_image, read_pxl, verify_pxl
from .crypto import generate_keypair

__version__ = "0.1.0"
__all__ = ["pack_image", "read_pxl", "verify_pxl", "generate_keypair"]