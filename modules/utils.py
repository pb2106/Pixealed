"""
Utility functions for chunking and CBOR canonicalization
"""

import cbor2
from typing import List, Any


def chunk_bytes(data: bytes, chunk_size: int) -> List[bytes]:
    """
    Split bytes into fixed-size chunks
    
    Args:
        data: Input bytes
        chunk_size: Size of each chunk in bytes
        
    Returns:
        List of byte chunks (last chunk may be smaller)
    """
    chunks = []
    offset = 0
    
    while offset < len(data):
        chunk = data[offset:offset + chunk_size]
        chunks.append(chunk)
        offset += chunk_size
    
    return chunks


def canonical_cbor(obj: Any) -> bytes:
    """
    Convert a Python object to canonical CBOR bytes
    
    Canonical format ensures consistent serialization for signing:
    - Keys sorted alphabetically
    
    Args:
        obj: Python object (dict, list, etc.)
        
    Returns:
        Canonical CBOR bytes
    """
    return cbor2.dumps(obj)