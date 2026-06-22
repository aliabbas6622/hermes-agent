"""
PROJECT NEXUS: Hive Memory System
Three-tier memory architecture: Semantic, Episodic, and Procedural.
Supports cross-device sync and vector similarity search.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.memory")

class MemoryType(Enum):
    SEMANTIC = "semantic"  # Facts, concepts, user preferences
    EPISODIC = "episodic"  # Events, experiences with timestamps
    PROCEDURAL = "procedural"  # Skills, task chains, successful workflows

@dataclass
class MemoryEntry:
    id: str
    memory_type: MemoryType
    content: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    importance: float = 1.0  # 0-1 scale for retention priority
    tags: List[str] = field(default_factory=list)
    source_device: Optional[str] = None
    embedding: Optional[List[float]] = None  # Vector embedding for similarity search
    metadata: Dict[str, Any] = field(default_factory=dict)

class VectorIndex:
    """Simple in-memory vector index for similarity search"""
    
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self.vectors: Dict[str, List[float]] = {}
    
    def add(self, entry_id: str, vector: List[float]):
        if len(vector) != self.dimensions:
            raise ValueError(f"Vector must be {self.dimensions} dimensions")
        self.vectors[entry_id] = vector
    
    def remove(self, entry_id: str):
        self.vectors.pop(entry_id, None)
    
    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """Find most similar vectors using cosine similarity"""
        if not self.vectors:
            return []
        
        def cosine_similarity(v1, v2):
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = sum(a * a for a in v1) ** 0.5
            norm2 = sum(b * b for b in v2) ** 0.5
            return dot / (norm1 * norm2) if norm1 and norm2 else 0
        
        scores = [
            (entry_id, cosine_similarity(query_vector, vec))
            for entry_id, vec in self.vectors.items()
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

class HiveMemory:
    """
    Unified memory system with three tiers:
    - Semantic: Long-term facts and knowledge
    - Episodic: Time-stamped events and experiences
    - Procedural: Learned skills and task patterns
    """
    
    def __init__(self, max_entries_per_type: int = 10000):
        self.semantic_memory: OrderedDict[str, MemoryEntry] = OrderedDict()
        self.episodic_memory: OrderedDict[str, MemoryEntry] = OrderedDict()
        self.procedural_memory: OrderedDict[str, MemoryEntry] = OrderedDict()
        
        self.vector_index = VectorIndex()
        self.max_entries = max_entries_per_type
        self._lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "total_writes": 0,
            "total_reads": 0,
            "similarity_searches": 0
        }
    
    async def store(self, memory_type: MemoryType, content: Any, 
                   tags: List[str] = None, importance: float = 1.0,
                   source_device: str = None, metadata: Dict = None) -> str:
        """Store a new memory entry"""
        async with self._lock:
            entry_id = hashlib.sha256(
                f"{time.time()}{json.dumps(content, sort_keys=True)}".encode()
            ).hexdigest()[:16]
            
            entry = MemoryEntry(
                id=entry_id,
                memory_type=memory_type,
                content=content,
                importance=importance,
                tags=tags or [],
                source_device=source_device,
                metadata=metadata or {}
            )
            
            # Select appropriate memory store
            memory_store = self._get_store(memory_type)
            
            # Add to store
            memory_store[entry_id] = entry
            memory_store.move_to_end(entry_id)  # Mark as recently used
            
            # Enforce capacity limits (remove least important)
            if len(memory_store) > self.max_entries:
                await self._forget_least_important(memory_store)
            
            self.stats["total_writes"] += 1
            logger.debug(f"Stored {memory_type.value} memory: {entry_id}")
            
            return entry_id
    
    async def retrieve(self, entry_id: str, memory_type: Optional[MemoryType] = None) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by ID"""
        async with self._lock:
            stores = [self._get_store(memory_type)] if memory_type else [
                self.semantic_memory, self.episodic_memory, self.procedural_memory
            ]
            
            for store in stores:
                if entry_id in store:
                    entry = store[entry_id]
                    entry.accessed_at = time.time()
                    entry.access_count += 1
                    store.move_to_end(entry_id)  # Mark as recently used
                    self.stats["total_reads"] += 1
                    return entry
            
            return None
    
    async def search_by_tags(self, tags: List[str], memory_type: Optional[MemoryType] = None,
                            limit: int = 10) -> List[MemoryEntry]:
        """Search memories by tags"""
        async with self._lock:
            stores = [self._get_store(memory_type)] if memory_type else [
                self.semantic_memory, self.episodic_memory, self.procedural_memory
            ]
            
            results = []
            for store in stores:
                for entry in store.values():
                    if any(tag in entry.tags for tag in tags):
                        results.append(entry)
                        if len(results) >= limit:
                            break
            
            # Sort by importance and recency
            results.sort(key=lambda e: (e.importance, e.accessed_at), reverse=True)
            return results[:limit]
    
    async def similarity_search(self, query_embedding: List[float], 
                               memory_type: Optional[MemoryType] = None,
                               top_k: int = 5) -> List[MemoryEntry]:
        """Find memories similar to the query embedding"""
        self.stats["similarity_searches"] += 1
        
        results = []
        matches = self.vector_index.similarity_search(query_embedding, top_k * 3)
        
        for entry_id, score in matches:
            entry = await self.retrieve(entry_id, memory_type)
            if entry:
                entry.metadata["similarity_score"] = score
                results.append(entry)
        
        return results[:top_k]
    
    async def learn_procedure(self, task_description: str, steps: List[Dict], 
                             success_rate: float, execution_time: float) -> str:
        """Store a successful task execution pattern as procedural memory"""
        content = {
            "task": task_description,
            "steps": steps,
            "success_rate": success_rate,
            "avg_execution_time": execution_time,
            "learned_at": time.time()
        }
        
        entry_id = await self.store(
            MemoryType.PROCEDURAL,
            content,
            tags=["procedure", "automation", task_description.split()[0]],
            importance=min(success_rate, 0.9),
            metadata={"category": "skill"}
        )
        
        logger.info(f"Learned new procedure: {task_description[:50]}...")
        return entry_id
    
    async def recall_similar_tasks(self, current_task: str, embedding: List[float]) -> Optional[Dict]:
        """Recall similar previously executed tasks for faster execution"""
        similar = await self.similarity_search(embedding, MemoryType.PROCEDURAL, top_k=1)
        
        if similar and similar[0].metadata.get("similarity_score", 0) > 0.7:
            proc = similar[0].content
            if proc.get("success_rate", 0) > 0.8:
                logger.info(f"Recalled successful procedure for: {current_task[:50]}")
                return proc
        
        return None
    
    async def _forget_least_important(self, store: OrderedDict):
        """Remove the least important memory to make space"""
        if not store:
            return
        
        # Find entry with lowest importance * recency score
        oldest_id = next(iter(store))
        lowest_score = float('inf')
        
        for entry_id, entry in list(store.items())[:100]:  # Check first 100
            recency = time.time() - entry.accessed_at
            score = entry.importance / (recency + 1)
            if score < lowest_score:
                lowest_score = score
                oldest_id = entry_id
        
        if oldest_id in store:
            del store[oldest_id]
            self.vector_index.remove(oldest_id)
            logger.debug(f"Forgetten memory: {oldest_id}")
    
    def _get_store(self, memory_type: MemoryType) -> OrderedDict:
        stores = {
            MemoryType.SEMANTIC: self.semantic_memory,
            MemoryType.EPISODIC: self.episodic_memory,
            MemoryType.PROCEDURAL: self.procedural_memory
        }
        return stores.get(memory_type, self.semantic_memory)
    
    def get_stats(self) -> Dict:
        return {
            "semantic_count": len(self.semantic_memory),
            "episodic_count": len(self.episodic_memory),
            "procedural_count": len(self.procedural_memory),
            **self.stats
        }

# Singleton instance
hive_memory = HiveMemory()

if __name__ == "__main__":
    async def demo():
        # Store some memories
        await hive_memory.store(
            MemoryType.SEMANTIC,
            {"fact": "User prefers Terminal 4 at JFK"},
            tags=["travel", "preference", "airport"],
            importance=0.9
        )
        
        await hive_memory.store(
            MemoryType.EPISODIC,
            {"event": "User flew to NYC", "date": "2024-01-15"},
            tags=["travel", "nyc"],
            importance=0.7
        )
        
        await hive_memory.learn_procedure(
            "Check flight status",
            [{"step": "open_email"}, {"step": "search_flight"}, {"step": "extract_status"}],
            success_rate=0.95,
            execution_time=12.5
        )
        
        # Search
        results = await hive_memory.search_by_tags(["travel"])
        print(f"\nFound {len(results)} travel-related memories:")
        for r in results:
            print(f"  - [{r.memory_type.value}] {r.content}")
        
        print(f"\nMemory Stats: {hive_memory.get_stats()}")
    
    asyncio.run(demo())
