"""
Utility functions for chunking and JSON canonicalization
"""

import json
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


def canonical_json(obj: Any) -> str:
    """
    Convert a Python object to canonical JSON string
    
    Canonical format ensures consistent serialization for signing:
    - Keys sorted alphabetically
    - No extra whitespace
    - Consistent formatting
    
    Args:
        obj: Python object (dict, list, etc.)
        
    Returns:
        Canonical JSON string
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True
    )