from datetime import datetime
from typing import Optional, List, Dict, Any

from ..database.qdrant_client import qdrant
from ..embeddings.generator import embedding_generator
from ..character.manager import character_manager
from ..config import MIN_ALIGNMENT_SCORE, MEMORY_TYPES

class MemoryManager:
    def __init__(self):
        self.qdrant = qdrant
        self.embedding_generator = embedding_generator
        self.character_manager = character_manager
    
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        source: str,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store a new memory if it aligns with Marvin's character
        """
        # Validate memory type
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Invalid memory type. Must be one of: {MEMORY_TYPES}")
        
        # Check character alignment
        alignment = self.character_manager.evaluate_alignment(content)
        
        if alignment["alignment_score"] < MIN_ALIGNMENT_SCORE:
            return None
        
        # Generate embedding
        vector = self.embedding_generator.generate(content)
        
        # Prepare payload
        payload = {
            "content": content,
            "type": memory_type,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or [],
            "persona_alignment_score": alignment["alignment_score"],
            "matched_aspects": alignment["matched_aspects"],
            "character_version": self.character_manager.get_current_character()["version"]
        }
        
        # Store in Qdrant
        return self.qdrant.store_memory(vector, payload)
    
    async def query_memories(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        min_alignment: float = MIN_ALIGNMENT_SCORE,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query memories based on semantic similarity
        """
        # Generate query embedding
        query_vector = self.embedding_generator.generate(query)
        
        # Prepare filters
        filter_conditions = {
            "must": [
                {
                    "key": "persona_alignment_score",
                    "range": {"gte": min_alignment}
                }
            ]
        }
        
        if memory_type:
            filter_conditions["must"].append({
                "key": "type",
                "match": {"value": memory_type}
            })
        
        if tags:
            filter_conditions["must"].append({
                "key": "tags",
                "match": {"value": tags}
            })
        
        # Query Qdrant
        results = self.qdrant.query_memories(
            query_vector=query_vector,
            limit=limit,
            filter_conditions=filter_conditions
        )
        
        return [
            {
                "id": point.id,
                "content": point.payload["content"],
                "type": point.payload["type"],
                "source": point.payload["source"],
                "timestamp": point.payload["timestamp"],
                "tags": point.payload["tags"],
                "alignment_score": point.payload["persona_alignment_score"],
                "similarity_score": point.score
            }
            for point in results
        ]
    
    def get_all_memories(
        self,
        memory_type: Optional[str] = None,
        min_alignment: float = MIN_ALIGNMENT_SCORE,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all memories with optional filtering
        """
        filter_conditions = {
            "must": [
                {
                    "key": "persona_alignment_score",
                    "range": {"gte": min_alignment}
                }
            ]
        }
        
        if memory_type:
            filter_conditions["must"].append({
                "key": "type",
                "match": {"value": memory_type}
            })
        
        if tags:
            filter_conditions["must"].append({
                "key": "tags",
                "match": {"value": tags}
            })
        
        memories = []
        for batch in self.qdrant.get_all_memories(filter=filter_conditions):
            memories.extend([
                {
                    "id": point.id,
                    "content": point.payload["content"],
                    "type": point.payload["type"],
                    "source": point.payload["source"],
                    "timestamp": point.payload["timestamp"],
                    "tags": point.payload["tags"],
                    "alignment_score": point.payload["persona_alignment_score"]
                }
                for point in batch
            ])
        
        return memories
    
    async def delete_memory(self, memory_id: str):
        """Delete a specific memory"""
        self.qdrant.delete_memory(memory_id)

# Create singleton instance
memory_manager = MemoryManager()
