from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from ..memory.manager import memory_manager
from ..research.research_manager import research_manager
from ..config import RESEARCH_AUTO_APPROVE

app = FastAPI(title="Marvin's Memory System")

# Models for research endpoints
class ResearchQuery(BaseModel):
    query: str
    auto_approve: Optional[bool] = None

class InsightApproval(BaseModel):
    insight_indices: List[int]

class MemoryInput(BaseModel):
    content: str
    type: str
    source: str
    tags: Optional[List[str]] = None

@app.post("/memories/")
async def create_memory(memory: MemoryInput):
    """Store a new memory"""
    try:
        memory_id = await memory_manager.store_memory(
            content=memory.content,
            memory_type=memory.type,
            source=memory.source,
            tags=memory.tags
        )
        
        if not memory_id:
            raise HTTPException(
                status_code=400,
                detail="Memory did not meet alignment threshold"
            )
        
        return {"id": memory_id}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/search")
async def search_memories(
    query: str,
    limit: int = 5,
    memory_type: Optional[str] = None,
    min_alignment: Optional[float] = None,
    tags: Optional[List[str]] = None
):
    """Search memories by semantic similarity"""
    try:
        memories = await memory_manager.query_memories(
            query=query,
            limit=limit,
            memory_type=memory_type,
            min_alignment=min_alignment,
            tags=tags
        )
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/")
async def list_memories(
    request: Request,
    memory_type: Optional[str] = None,
    min_alignment: Optional[float] = None,
    tags: Optional[List[str]] = None
):
    """List all memories with optional filtering"""
    logger.debug(f"list_memories called with memory_type={memory_type}, min_alignment={min_alignment}, tags={tags}")
    logger.debug(f"Request query params: {request.query_params}")
    
    try:
        logger.debug("Calling memory_manager.get_all_memories")
        memories = memory_manager.get_all_memories(
            memory_type=memory_type,
            min_alignment=min_alignment,
            tags=tags
        )
        logger.debug(f"get_all_memories returned {len(memories)} memories")
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error in list_memories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory"""
    try:
        await memory_manager.delete_memory(memory_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Research endpoints
@app.post("/research/")
async def conduct_research(research: ResearchQuery):
    """Conduct research using Perplexity API"""
    try:
        result = await research_manager.conduct_research(
            query=research.query,
            auto_approve=research.auto_approve
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error")
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/research/")
async def get_pending_research():
    """Get all pending research"""
    try:
        pending = await research_manager.get_pending_research()
        return {"pending_research": pending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/research/{query_id}")
async def get_pending_research_by_id(query_id: str):
    """Get pending research by ID"""
    try:
        pending = await research_manager.get_pending_research_by_id(query_id)
        
        if not pending:
            raise HTTPException(
                status_code=404,
                detail="Research not found"
            )
        
        return pending
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{query_id}/approve")
async def approve_insights(query_id: str, approval: InsightApproval):
    """Approve selected insights for storage"""
    try:
        result = await research_manager.approve_insights(
            query_id=query_id,
            insight_indices=approval.insight_indices
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Unknown error")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/research/{query_id}")
async def reject_research(query_id: str):
    """Reject and delete pending research"""
    try:
        result = await research_manager.reject_research(query_id)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Unknown error")
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/research")
async def get_research_settings():
    """Get research settings"""
    return {
        "auto_approve": RESEARCH_AUTO_APPROVE
    }
