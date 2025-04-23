from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid
from datetime import datetime

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
        return self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            filter=filter_conditions
        )
    
    def get_all_memories(self, batch_size=100, filter=None):
        """Get all memories with pagination"""
        offset = None
        while True:
            results = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=batch_size,
                offset=offset,
                filter=filter
            )[0]  # scroll returns (points, next_offset)
            
            if not results:
                break
                
            yield results
            
            if len(results) < batch_size:
                break
    
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
