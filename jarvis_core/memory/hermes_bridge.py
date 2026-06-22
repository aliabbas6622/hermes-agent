"""
Hermes Memory Integration Layer
Bridges TurboQuant compressed vectors with Hermes native memory system.
Provides context-aware retrieval without bloating LLM token usage.
"""

import os
import json
import time
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

# Import our quantization engine
from jarvis_core.quant.turbo_quant import TurboQuantEncoder, QuantizedMemoryIndex

@dataclass
class MemoryEntry:
    id: int
    content: str
    embedding_id: int  # Reference to quantized vector
    category: str
    timestamp: float
    importance: float  # 0.0-1.0 score for retention priority
    metadata: Dict
    
class HermesMemoryBridge:
    """
    Integrates with Hermes' existing SQLite memory while adding:
    1. TurboQuant compression for embeddings
    2. Importance-based forgetting mechanism
    3. Context-aware retrieval with compressed vectors
    4. Token-efficient context window construction
    """
    
    def __init__(self, db_path: str = "hermes_memory.db", embedding_dim: int = 768):
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.quant_index = QuantizedMemoryIndex(dim=embedding_dim)
        self.encoder = TurboQuantEncoder(dim=embedding_dim)
        
        # In-memory cache for recent entries (avoid DB hits)
        self.recent_cache: List[MemoryEntry] = []
        self.cache_size = 50
        
        self._init_db()
        
    def _init_db(self):
        """Initialize or connect to Hermes memory database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if not exist (compatible with Hermes schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                timestamp REAL,
                importance REAL DEFAULT 0.5,
                metadata TEXT,
                embedding_ref INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
        
    def store(self, content: str, category: str = "general", 
              embedding: Optional[np.ndarray] = None, 
              importance: float = 0.5,
              metadata: Dict = None) -> int:
        """
        Store a memory with compressed embedding.
        
        Args:
            content: Text content of memory
            category: Category tag (e.g., "user_preference", "task_history")
            embedding: Pre-computed embedding vector (if None, will use placeholder)
            importance: Retention priority (0.0-1.0)
            metadata: Additional JSON-serializable data
            
        Returns:
            Memory ID
        """
        # Generate or use provided embedding
        if embedding is None:
            # Placeholder: In production, call embedding model here
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
        
        # Compress and store in quantized index
        emb_id = self.quant_index.add(embedding, meta={'category': category, 'time': time.time()})
        
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (content, category, timestamp, importance, metadata, embedding_ref)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (content, category, time.time(), importance, 
              json.dumps(metadata or {}), emb_id))
        
        mem_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update cache
        entry = MemoryEntry(
            id=mem_id,
            content=content,
            embedding_id=emb_id,
            category=category,
            timestamp=time.time(),
            importance=importance,
            metadata=metadata or {}
        )
        self.recent_cache.append(entry)
        if len(self.recent_cache) > self.cache_size:
            self.recent_cache.pop(0)
            
        return mem_id
    
    def retrieve_relevant(self, query: str, query_embedding: Optional[np.ndarray] = None,
                         top_k: int = 5, category_filter: Optional[str] = None,
                         min_importance: float = 0.0) -> List[Dict]:
        """
        Retrieve relevant memories using compressed vector search.
        
        Args:
            query: Search query text
            query_embedding: Pre-computed query embedding
            top_k: Number of results
            category_filter: Optional category filter
            min_importance: Minimum importance threshold
            
        Returns:
            List of memory dicts with content and metadata
        """
        # Generate or use provided query embedding
        if query_embedding is None:
            # Placeholder: In production, call embedding model here
            query_embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search in quantized index
        results = self.quant_index.search(query_embedding, top_k=top_k * 2)  # Get extra for filtering
        
        # Fetch full details from DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        relevant_memories = []
        for emb_id, similarity, emb_meta in results:
            # Apply filters
            if category_filter and emb_meta.get('category') != category_filter:
                continue
                
            cursor.execute('''
                SELECT id, content, category, timestamp, importance, metadata
                FROM memories WHERE embedding_ref = ? AND importance >= ?
            ''', (emb_id, min_importance))
            
            row = cursor.fetchone()
            if row:
                relevant_memories.append({
                    'id': row[0],
                    'content': row[1],
                    'category': row[2],
                    'timestamp': row[3],
                    'importance': row[4],
                    'metadata': json.loads(row[5]),
                    'similarity': similarity
                })
                
        conn.close()
        
        # Sort by combined score (similarity * importance)
        relevant_memories.sort(
            key=lambda x: x['similarity'] * (0.5 + 0.5 * x['importance']), 
            reverse=True
        )
        
        return relevant_memories[:top_k]
    
    def get_context_window(self, current_topic: str, 
                          max_tokens: int = 2000,
                          include_recent: int = 5) -> str:
        """
        Build an optimized context window for LLM calls.
        
        Strategy:
        1. Always include N most recent memories
        2. Add relevant memories based on topic similarity
        3. Compress/summarize older entries to save tokens
        4. Stop when approaching token limit
        
        Args:
            current_topic: Current conversation/task topic
            max_tokens: Maximum token budget
            include_recent: Number of recent memories to always include
            
        Returns:
            Formatted context string
        """
        # Estimate: 1 token ≈ 4 characters (rough average)
        max_chars = max_tokens * 4
        
        context_parts = []
        current_length = 0
        
        # 1. Add recent memories (always relevant)
        recent = self.recent_cache[-include_recent:] if self.recent_cache else []
        for mem in reversed(recent):
            entry = f"[Recent] {mem.content}\n"
            if current_length + len(entry) < max_chars:
                context_parts.insert(0, entry)  # Prepend to keep chronological
                current_length += len(entry)
        
        # 2. Add relevant memories based on topic
        # In production: generate embedding for current_topic
        relevant = self.retrieve_relevant(
            query=current_topic,
            top_k=10,
            min_importance=0.3
        )
        
        for mem in relevant:
            entry = f"[Relevant:{mem['category']}] {mem['content']}\n"
            if current_length + len(entry) < max_chars:
                context_parts.append(entry)
                current_length += len(entry)
            else:
                break
        
        # 3. Add summary of older high-importance memories if space allows
        if current_length < max_chars * 0.8:
            # Could add aggregated summaries here
            pass
        
        return "".join(context_parts)
    
    def decay_importance(self, days_old: float, decay_factor: float = 0.95):
        """
        Apply time-based decay to memory importance.
        Run periodically to forget irrelevant old memories.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        cursor.execute('''
            UPDATE memories 
            SET importance = importance * ?
            WHERE timestamp < ? AND importance > 0.1
        ''', (decay_factor, cutoff_time))
        
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return updated
    
    def cleanup_low_importance(self, threshold: float = 0.1):
        """Remove memories with very low importance to save space."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM memories WHERE importance < ?', (threshold,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_stats(self) -> Dict:
        """Return memory system statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM memories')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(importance) FROM memories')
        avg_importance = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT category, COUNT(*) FROM memories GROUP BY category')
        categories = dict(cursor.fetchall())
        
        conn.close()
        
        quant_stats = self.quant_index.get_stats()
        
        return {
            'total_memories': total,
            'average_importance': round(avg_importance, 3),
            'categories': categories,
            'cache_size': len(self.recent_cache),
            'quant_compression_ratio': quant_stats.get('compression_ratio', 0),
            'quant_storage_kb': quant_stats.get('compressed_kb', 0)
        }
