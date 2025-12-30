"""Query API - SAGE-Flow natural language queries."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    verbose: bool = False


class QueryResponse(BaseModel):
    question: str
    intent: str
    answer: str
    execution_order: str
    timing: Dict[str, float]
    success: bool


def get_orchestrator():
    from api.main import _sage_flow
    if _sage_flow is None:
        raise HTTPException(status_code=500, detail="SAGE-Flow not initialized")
    return _sage_flow


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Execute a natural language query through SAGE-Flow."""
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.query(request.question)
        
        return QueryResponse(
            question=request.question,
            intent=result.intent.value if hasattr(result.intent, 'value') else str(result.intent),
            answer=result.answer,
            execution_order=result.execution_order,
            timing={
                "routing": result.routing_time,
                "sql": result.sql_time,
                "graph": result.graph_time,
                "merge": result.merge_time,
                "total": result.total_time
            },
            success=result.success
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def status():
    """Check SAGE-Flow status."""
    try:
        orchestrator = get_orchestrator()
        return {
            "status": "ready",
            "graph_nodes": orchestrator.graph_agent.graph.number_of_nodes() if orchestrator.graph_agent else 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
