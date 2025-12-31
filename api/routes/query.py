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
    thought_process: Optional[str] = None
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
        
        # Handle dictionary response from SAGEAgent
        if isinstance(result, dict):
            raw_output = result.get("output", "")
            thought = None
            answer = raw_output
            
            # Extract thinking process if present
            if "<think>" in raw_output and "</think>" in raw_output:
                start = raw_output.find("<think>")
                end = raw_output.find("</think>")
                thought = raw_output[start + 7 : end].strip()
                answer = raw_output[end + 8:].strip()
            
            return QueryResponse(
                question=request.question,
                intent="query", # Default intent
                answer=answer,
                thought_process=thought,
                execution_order="graph_rag",
                timing={
                    "total": 0.0 # Timing not exposed in new agent
                },
                success=not result.get("error", False)
            )
            
        # Fallback for object-based response (legacy)
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
