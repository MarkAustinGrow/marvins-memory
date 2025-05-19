from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid
from datetime import datetime
import logging
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from ..config import (
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    VECTOR_SIZE
)

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists with correct configuration"""
        collections = self.client.get_collections().collections
        exists = any(col.name == COLLECTION_NAME for col in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
    
    def store_memory(self, vector, payload):
        """Store a memory point in Qdrant"""
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        return point_id
    
    def query_memories(self, query_vector, limit=5, filter_conditions=None):
        """Query similar memories"""
        logger.debug(f"query_memories called with filter: {json.dumps(filter_conditions) if filter_conditions else None}")
        
        try:
            # Try with filter first
            if filter_conditions:
                logger.debug(f"Attempting search with filter: {json.dumps(filter_conditions)}")
                return self.client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=limit,
                    filter=filter_conditions
                )
            else:
                # No filter provided
                return self.client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=limit
                )
        except Exception as e:
            logger.error(f"Error in search with filter: {str(e)}")
            
            # Try without filter as fallback
            logger.debug("Trying search without filter as fallback")
            try:
                results = self.client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=limit
                )
                logger.debug(f"Fallback search returned {len(results)} results")
                return results
            except Exception as fallback_error:
                logger.error(f"Error in fallback search: {str(fallback_error)}")
                # Re-raise the original error if fallback also fails
                raise e
    
    def get_all_memories(self, batch_size=100, filter=None):
        """
        Get all memories with pagination (generator)
        
        This method is a generator that yields batches of memories.
        For most use cases, get_memories_paginated is more appropriate.
        """
        logger.debug(f"get_all_memories called with filter: {json.dumps(filter) if filter else None}")
        logger.debug(f"filter type: {type(filter)}")
        logger.debug(f"filter keys: {filter.keys() if filter and hasattr(filter, 'keys') else 'No keys'}")
        
        # Try to fix the filter format if needed
        fixed_filter = self._fix_filter_format(filter)
        
        offset = None
        while True:
            try:
                logger.debug(f"Calling scroll with filter: {json.dumps(fixed_filter if fixed_filter else filter, default=str)}")
                try:
                    results = self.client.scroll(
                        collection_name=COLLECTION_NAME,
                        limit=batch_size,
                        offset=offset,
                        filter=fixed_filter if fixed_filter else filter
                    )[0]  # scroll returns (points, next_offset)
                    logger.debug(f"scroll returned {len(results) if results else 0} results")
                except Exception as e:
                    logger.error(f"Error in scroll: {str(e)}")
                    # Try without filter as a fallback
                    logger.debug("Trying without filter as fallback")
                    results = self.client.scroll(
                        collection_name=COLLECTION_NAME,
                        limit=batch_size,
                        offset=offset
                    )[0]
                    logger.debug(f"Fallback scroll returned {len(results) if results else 0} results")
                
                if not results:
                    break
                    
                yield results
                
                if len(results) < batch_size:
                    break
            except Exception as e:
                logger.error(f"Error in get_all_memories: {str(e)}")
                break
    
    def get_memories_paginated(self, offset=0, limit=50, filter=None):
        """
        Get memories with pagination (single batch)
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            filter: Filter conditions
            
        Returns:
            List of memory points
        """
        logger.debug(f"get_memories_paginated called with offset={offset}, limit={limit}, filter={json.dumps(filter) if filter else None}")
        
        # Try to fix the filter format if needed
        fixed_filter = self._fix_filter_format(filter)
        
        try:
            # Try with filter first
            try:
                logger.debug(f"Calling scroll with filter: {json.dumps(fixed_filter if fixed_filter else filter, default=str)}")
                results = self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=limit,
                    offset=offset,
                    filter=fixed_filter if fixed_filter else filter
                )[0]  # scroll returns (points, next_offset)
                logger.debug(f"scroll returned {len(results) if results else 0} results")
                return results
            except Exception as e:
                logger.error(f"Error in scroll with filter: {str(e)}")
                # Try without filter as a fallback
                logger.debug("Trying without filter as fallback")
                results = self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=limit,
                    offset=offset
                )[0]
                logger.debug(f"Fallback scroll returned {len(results) if results else 0} results")
                return results
        except Exception as e:
            logger.error(f"Error in get_memories_paginated: {str(e)}")
            return []
    
    def count_memories(self, filter=None):
        """
        Count total memories matching the filter criteria
        
        Args:
            filter: Filter conditions
            
        Returns:
            Total count of matching memories
        """
        logger.debug(f"count_memories called with filter: {json.dumps(filter) if filter else None}")
        
        # Try to fix the filter format if needed
        fixed_filter = self._fix_filter_format(filter)
        
        try:
            # Try with filter first
            try:
                logger.debug(f"Calling count with filter: {json.dumps(fixed_filter if fixed_filter else filter, default=str)}")
                count = self.client.count(
                    collection_name=COLLECTION_NAME,
                    count_filter=fixed_filter if fixed_filter else filter
                ).count
                logger.debug(f"count returned {count}")
                return count
            except Exception as e:
                logger.error(f"Error in count with filter: {str(e)}")
                # Try without filter as a fallback
                logger.debug("Trying count without filter as fallback")
                count = self.client.count(
                    collection_name=COLLECTION_NAME
                ).count
                logger.debug(f"Fallback count returned {count}")
                return count
        except Exception as e:
            logger.error(f"Error in count_memories: {str(e)}")
            return 0
    
    def _fix_filter_format(self, filter):
        """
        Fix filter format to be compatible with Qdrant
        
        Args:
            filter: Filter conditions
            
        Returns:
            Fixed filter or None if filter is None
        """
        if not filter:
            return None
            
        fixed_filter = None
        if isinstance(filter, dict):
            # Log the structure of the filter
            logger.debug(f"Filter structure: {json.dumps(filter, default=str)}")
            
            # Check if the filter has the expected structure
            if "must" in filter and isinstance(filter["must"], list):
                # This is the correct format for Qdrant
                fixed_filter = filter
                logger.debug("Using original filter format")
            else:
                # Try to convert to the correct format
                logger.debug("Attempting to fix filter format")
                fixed_filter = {"must": []}
                for key, value in filter.items():
                    if isinstance(value, dict) and "range" in value:
                        fixed_filter["must"].append({"range": {key: value["range"]}})
                    elif isinstance(value, dict) and "match" in value:
                        fixed_filter["must"].append({"match": {key: value["match"]["value"]}})
                logger.debug(f"Fixed filter: {json.dumps(fixed_filter, default=str)}")
        
        return fixed_filter
    
    def update_memory(self, point_id, payload):
        """Update memory payload"""
        self.client.set_payload(
            collection_name=COLLECTION_NAME,
            points=[point_id],
            payload=payload
        )
    
    def delete_memory(self, point_id):
        """Delete a memory point"""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[point_id]
        )

# Create singleton instance
qdrant = QdrantManager()
