"""
Merkle tree utilities for chunk integrity verification
"""

import blake3
from typing import List, Tuple


def hash_chunk(data: bytes) -> str:
    """
    Compute BLAKE3 hash of a single chunk
    
    Args:
        data: Chunk bytes
        
    Returns:
        Hex-encoded hash string
    """
    return blake3.blake3(data).hexdigest()


def build_merkle_tree(chunks: List[bytes]) -> Tuple[str, List[str]]:
    """
    Build a Merkle tree from chunks and return the root hash
    
    Args:
        chunks: List of byte chunks
        
    Returns:
        Tuple of (merkle_root_hex, list_of_chunk_hashes_hex)
    """
    if not chunks:
        raise ValueError("Cannot build Merkle tree from empty chunks")
    
    # Hash all chunks
    chunk_hashes = [hash_chunk(chunk) for chunk in chunks]
    
    # Build Merkle tree
    current_level = chunk_hashes[:]
    
    while len(current_level) > 1:
        next_level = []
        
        # Process pairs
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            
            # If odd number of nodes, duplicate the last one
            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left
            
            # Hash the concatenation
            combined = left + right
            parent_hash = blake3.blake3(combined.encode()).hexdigest()
            next_level.append(parent_hash)
        
        current_level = next_level
    
    # Root is the last remaining hash
    merkle_root = current_level[0]
    
    return merkle_root, chunk_hashes


def verify_chunk(chunk: bytes, expected_hash: str) -> bool:
    """
    Verify a single chunk against its expected hash
    
    Args:
        chunk: Chunk bytes
        expected_hash: Expected hex-encoded hash
        
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = hash_chunk(chunk)
    return actual_hash == expected_hash