from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json

from ..database.qdrant_client import qdrant
from ..embeddings.generator import embedding_generator
from ..character.manager import character_manager
from ..config import MIN_ALIGNMENT_SCORE, MEMORY_TYPES

# Set up logging
logger = logging.getLogger(__name__)

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
        tags: Optional[List[str]] = None,
        bypass_alignment_check: bool = False  # New parameter
    ) -> str:
        """
        Store a new memory if it aligns with Marvin's character or if alignment check is bypassed
        """
        # Validate memory type
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Invalid memory type. Must be one of: {MEMORY_TYPES}")
        
        # Check character alignment (unless bypassed)
        alignment_score = MIN_ALIGNMENT_SCORE  # Default value
        matched_aspects = []
        alignment_explanation = "Alignment check bypassed"
        
        if not bypass_alignment_check:
            # Perform the alignment check as before
            alignment = self.character_manager.evaluate_alignment(content)
            
            # Add error handling for alignment
            if alignment is None:
                logger.error("Character alignment evaluation returned None")
                alignment = {
                    "alignment_score": MIN_ALIGNMENT_SCORE,
                    "matched_aspects": ["error_fallback"],
                    "explanation": "Error in alignment evaluation - using minimum score"
                }
            
            alignment_score = alignment.get("alignment_score", 0)
            matched_aspects = alignment.get("matched_aspects", [])
            alignment_explanation = alignment.get("explanation", "No explanation provided")
            
            if alignment_score < MIN_ALIGNMENT_SCORE:
                logger.debug(f"Content rejected: alignment score {alignment_score} below threshold {MIN_ALIGNMENT_SCORE}")
                return None
        else:
            logger.debug("Alignment check bypassed for this memory")
        
        logger.debug(f"Content accepted: alignment score {alignment_score if not bypass_alignment_check else 'bypassed'}")
        
        # Generate embedding
        vector = self.embedding_generator.generate(content)
        
        # Prepare payload
        character_data = self.character_manager.get_current_character()
        character_version = character_data.get("version", "unknown") if character_data else "unknown"
        
        payload = {
            "content": content,
            "type": memory_type,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or [],
            "persona_alignment_score": alignment_score,
            "matched_aspects": matched_aspects,
            "alignment_explanation": alignment_explanation,
            "character_version": character_version,
            "alignment_bypassed": bypass_alignment_check
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
        logger.debug(f"query_memories called with query='{query}', limit={limit}, memory_type={memory_type}, min_alignment={min_alignment}, tags={tags}")
        
        try:
            # Generate query embedding
            query_vector = self.embedding_generator.generate(query)
            logger.debug(f"Generated embedding vector of length {len(query_vector)}")
            
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
            
            logger.debug(f"Constructed filter: {json.dumps(filter_conditions)}")
            
            # Query Qdrant
            logger.debug("Calling qdrant.query_memories")
            results = self.qdrant.query_memories(
                query_vector=query_vector,
                limit=limit,
                filter_conditions=filter_conditions
            )
            
            logger.debug(f"Query returned {len(results)} results")
            
            # Process results
            memories = []
            for point in results:
                try:
                    memory = {
                        "id": point.id,
                        "content": point.payload["content"],
                        "type": point.payload["type"],
                        "source": point.payload["source"],
                        "timestamp": point.payload["timestamp"],
                        "tags": point.payload["tags"],
                        "alignment_score": point.payload["persona_alignment_score"],
                        "similarity_score": point.score
                    }
                    memories.append(memory)
                except Exception as e:
                    logger.error(f"Error processing result point: {str(e)}")
                    # Continue with other results
            
            logger.debug(f"Returning {len(memories)} processed memories")
            return memories
            
        except Exception as e:
            logger.error(f"Error in query_memories: {str(e)}")
            logger.error(f"Traceback: {logging.traceback.format_exc()}")
            # Return empty list instead of raising exception
            return []
    
    def get_all_memories(
        self,
        memory_type: Optional[str] = None,
        min_alignment: float = MIN_ALIGNMENT_SCORE,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all memories with optional filtering
        """
        logger.debug(f"get_all_memories called with memory_type={memory_type}, min_alignment={min_alignment}, tags={tags}")
        
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
        
        logger.debug(f"Constructed filter: {json.dumps(filter_conditions)}")
        
        memories = []
        try:
            logger.debug("Calling qdrant.get_all_memories")
            for batch in self.qdrant.get_all_memories(filter=filter_conditions):
                logger.debug(f"Received batch with {len(batch)} items")
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
        except Exception as e:
            logger.error(f"Error in get_all_memories: {str(e)}")
        
        return memories
    
    async def delete_memory(self, memory_id: str):
        """Delete a specific memory"""
        self.qdrant.delete_memory(memory_id)

# Create singleton instance
memory_manager = MemoryManager()
