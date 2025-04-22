from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..memory.manager import memory_manager

app = FastAPI(title="Marvin's Memory System")

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
    memory_type: Optional[str] = None,
    min_alignment: Optional[float] = None,
    tags: Optional[List[str]] = None
):
    """List all memories with optional filtering"""
    try:
        memories = await memory_manager.get_all_memories(
            memory_type=memory_type,
            min_alignment=min_alignment,
            tags=tags
        )
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory"""
    try:
        await memory_manager.delete_memory(memory_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 