from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..config import RESEARCH_AUTO_APPROVE, RESEARCH_MAX_INSIGHTS
from ..memory.manager import memory_manager
from .perplexity_client import perplexity_client

class ResearchManager:
    """Manager for research operations and integration with memory system"""
    
    def __init__(self):
        self.perplexity_client = perplexity_client
        self.memory_manager = memory_manager
        self.pending_insights = {}  # Store pending insights by query ID
    
    async def conduct_research(self, query: str, auto_approve: Optional[bool] = None) -> Dict[str, Any]:
        """
        Conduct research using Perplexity API
        
        Args:
            query: The research question
            auto_approve: Override the default auto-approve setting
            
        Returns:
            Dictionary with query ID, insights, and status
        """
        # Determine if we should auto-approve
        should_auto_approve = auto_approve if auto_approve is not None else RESEARCH_AUTO_APPROVE
        
        try:
            # Query Perplexity API
            response = await self.perplexity_client.query(query)
            
            # Extract insights
            insights = await self.perplexity_client.extract_insights(response)
            
            # Generate a query ID
            query_id = f"research_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Store insights for later approval if not auto-approving
            if not should_auto_approve:
                self.pending_insights[query_id] = {
                    "query": query,
                    "insights": insights,
                    "timestamp": datetime.now().isoformat(),
                    "raw_response": response
                }
                
                return {
                    "query_id": query_id,
                    "insights": insights,
                    "status": "pending_approval",
                    "auto_approved": False,
                    "count": len(insights)
                }
            
            # Auto-approve: store insights directly
            stored_memories = await self._store_insights(query, insights)
            
            return {
                "query_id": query_id,
                "insights": insights,
                "status": "stored",
                "auto_approved": True,
                "stored_count": len(stored_memories),
                "memory_ids": [memory["id"] for memory in stored_memories if "id" in memory]
            }
            
        except Exception as e:
            logging.error(f"Error conducting research: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_pending_research(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all pending research insights
        
        Returns:
            Dictionary of pending research by query ID
        """
        return self.pending_insights
    
    async def get_pending_research_by_id(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pending research by ID
        
        Args:
            query_id: The query ID
            
        Returns:
            The pending research or None if not found
        """
        return self.pending_insights.get(query_id)
    
    async def approve_insights(self, query_id: str, insight_indices: List[int]) -> Dict[str, Any]:
        """
        Approve selected insights for storage
        
        Args:
            query_id: The query ID
            insight_indices: Indices of insights to approve
            
        Returns:
            Status of the approval operation
        """
        if query_id not in self.pending_insights:
            return {
                "status": "error",
                "error": "Query ID not found"
            }
        
        pending = self.pending_insights[query_id]
        insights = pending["insights"]
        
        # Validate indices
        valid_indices = [i for i in insight_indices if 0 <= i < len(insights)]
        
        if not valid_indices:
            return {
                "status": "error",
                "error": "No valid insight indices provided"
            }
        
        # Get selected insights
        selected_insights = [insights[i] for i in valid_indices]
        
        # Store insights
        stored_memories = await self._store_insights(pending["query"], selected_insights)
        
        # Remove from pending if all insights were processed
        if set(valid_indices) == set(range(len(insights))):
            del self.pending_insights[query_id]
        
        return {
            "status": "stored",
            "query_id": query_id,
            "stored_count": len(stored_memories),
            "memory_ids": [memory["id"] for memory in stored_memories if "id" in memory]
        }
    
    async def reject_research(self, query_id: str) -> Dict[str, Any]:
        """
        Reject and delete pending research
        
        Args:
            query_id: The query ID
            
        Returns:
            Status of the rejection operation
        """
        if query_id not in self.pending_insights:
            return {
                "status": "error",
                "error": "Query ID not found"
            }
        
        del self.pending_insights[query_id]
        
        return {
            "status": "rejected",
            "query_id": query_id
        }
    
    async def _store_insights(self, query: str, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Store insights in memory
        
        Args:
            query: The original query
            insights: List of insights to store
            
        Returns:
            List of stored memories
        """
        # Format insights for memory storage
        memories = await self.perplexity_client.format_for_memory(insights)
        
        # Store each memory
        stored_memories = []
        for memory in memories:
            memory_id = await self.memory_manager.store_memory(
                content=memory["content"],
                memory_type=memory["type"],
                source=memory["source"],
                tags=memory["tags"]
            )
            
            if memory_id:
                stored_memories.append({
                    "id": memory_id,
                    "content": memory["content"],
                    "type": memory["type"]
                })
        
        return stored_memories

# Create singleton instance
research_manager = ResearchManager()
