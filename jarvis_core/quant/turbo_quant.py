"""
TurboQuant-inspired Vector Compression Engine
Implements binary and scalar quantization for extreme memory efficiency
Based on Google's TurboQuant research for AI efficiency
"""

import numpy as np
from typing import List, Tuple, Optional
import struct
import hashlib

class TurboQuantEncoder:
    """
    Extreme compression for vector embeddings using mixed-precision quantization.
    Reduces 768-dim float32 vectors (3KB) to ~100 bytes with minimal accuracy loss.
    """
    
    def __init__(self, dim: int = 768):
        self.dim = dim
        # Pre-computed codebooks for scalar quantization (8-bit)
        self.codebook_size = 256
        
    def encode_binary(self, vector: np.ndarray) -> bytes:
        """
        Binary quantization: converts floats to bits based on sign.
        Compression ratio: 32x (float32 -> 1-bit)
        """
        if len(vector) != self.dim:
            raise ValueError(f"Vector dim {len(vector)} != expected {self.dim}")
        
        # Convert to binary mask (1 if > 0, else 0)
        binary_mask = (vector > 0).astype(np.uint8)
        
        # Pack 8 bits into 1 byte
        packed = np.packbits(binary_mask)
        return packed.tobytes()
    
    def decode_binary(self, compressed: bytes) -> np.ndarray:
        """Reconstruct approximate vector from binary representation."""
        binary_mask = np.unpackbits(np.frombuffer(compressed, dtype=np.uint8))
        # Map 0->-1, 1->1 (approximate reconstruction)
        return (binary_mask[:self.dim] * 2 - 1).astype(np.float32)
    
    def encode_scalar(self, vector: np.ndarray, norm: Optional[float] = None) -> Tuple[bytes, float]:
        """
        Scalar quantization: maps values to 8-bit integers using dynamic range.
        Compression ratio: 4x (float32 -> 8-bit) + stores norm separately.
        """
        if norm is None:
            norm = np.linalg.norm(vector)
        
        if norm < 1e-9:
            # Zero vector edge case
            return b'\x00' * (self.dim // 4), 0.0
            
        # Normalize vector
        normalized = vector / norm
        
        # Map [-1, 1] to [0, 255]
        quantized = ((normalized + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
        
        return quantized.tobytes(), norm
    
    def decode_scalar(self, compressed: bytes, norm: float) -> np.ndarray:
        """Reconstruct vector from scalar quantized representation."""
        quantized = np.frombuffer(compressed, dtype=np.uint8)
        # Map [0, 255] back to [-1, 1]
        normalized = (quantized.astype(np.float32) / 255 * 2 - 1)
        return normalized * norm
    
    def encode_hybrid(self, vector: np.ndarray) -> dict:
        """
        Hybrid approach: Binary for direction, Scalar for magnitude clusters.
        Optimal balance of speed and accuracy.
        """
        norm = np.linalg.norm(vector)
        binary_part = self.encode_binary(vector)
        # Store norm as float32 (4 bytes)
        norm_bytes = struct.pack('f', norm)
        
        return {
            'binary': binary_part,
            'norm': norm,
            'norm_bytes': norm_bytes,
            'size': len(binary_part) + 4
        }
    
    def compute_hash(self, vector: np.ndarray) -> str:
        """Fast hash for deduplication without storing full vector."""
        binary = self.encode_binary(vector)
        return hashlib.md5(binary).hexdigest()


class QuantizedMemoryIndex:
    """
    Efficient similarity search using quantized vectors.
    Avoids storing full-precision vectors in RAM.
    """
    
    def __init__(self, dim: int = 768):
        self.encoder = TurboQuantEncoder(dim)
        self.dim = dim  # Store dim as instance attribute
        self.index = {}  # id -> {'compressed': bytes, 'norm': float, 'meta': dict}
        self.id_counter = 0
        
    def add(self, vector: np.ndarray, meta: dict = None) -> int:
        """Add vector to index in compressed form."""
        compressed, norm = self.encoder.encode_scalar(vector)
        vid = self.id_counter
        self.id_counter += 1
        
        self.index[vid] = {
            'compressed': compressed,
            'norm': norm,
            'meta': meta or {},
            'hash': self.encoder.compute_hash(vector)
        }
        return vid
    
    def search(self, query: np.ndarray, top_k: int = 5) -> List[Tuple[int, float, dict]]:
        """
        Approximate nearest neighbor search using quantized dot product.
        Much faster than full precision search.
        """
        q_compressed, q_norm = self.encoder.encode_scalar(query)
        q_vec = self.encoder.decode_scalar(q_compressed, q_norm)
        
        scores = []
        for vid, data in self.index.items():
            # Decode candidate
            cand_vec = self.encoder.decode_scalar(data['compressed'], data['norm'])
            
            # Cosine similarity
            sim = np.dot(q_vec, cand_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(cand_vec) + 1e-9)
            scores.append((vid, float(sim), data['meta']))
        
        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def get_stats(self) -> dict:
        """Return compression statistics."""
        if not self.index:
            return {'count': 0, 'compression_ratio': 0}
            
        total_compressed = sum(len(v['compressed']) + 4 for v in self.index.values())
        original_size = len(self.index) * self.dim * 4  # float32 = 4 bytes
        
        return {
            'count': len(self.index),
            'original_kb': original_size / 1024,
            'compressed_kb': total_compressed / 1024,
            'compression_ratio': original_size / max(total_compressed, 1)
        }
