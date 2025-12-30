"""Actions API - Agentic workflow execution endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class ActionRequest(BaseModel):
    action: str


class ActionResponse(BaseModel):
    action_id: str
    action_type: str
    status: str
    message: str
    output: Optional[Any] = None
    steps_executed: List[str] = []
    execution_time_ms: int = 0


class AvailableAction(BaseModel):
    action: str
    example: str


def get_action_executor():
    from api.main import _action_executor
    if _action_executor is None:
        raise HTTPException(status_code=500, detail="ActionExecutor not initialized")
    return _action_executor


@router.post("/execute", response_model=ActionResponse)
async def execute_action(request: ActionRequest):
    """Execute a natural language action request."""
    try:
        executor = get_action_executor()
        result = executor.execute(request.action)
        
        output = result.output
        if hasattr(output, 'to_dict'):
            output = output.to_dict()
        elif not isinstance(output, (dict, list, str, int, float, bool, type(None))):
            output = str(output)
        
        return ActionResponse(
            action_id=result.action_id,
            action_type=result.action_type.value,
            status=result.status.value,
            message=result.message,
            output=output,
            steps_executed=result.steps_executed,
            execution_time_ms=result.execution_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available", response_model=List[AvailableAction])
async def get_available_actions():
    """Get list of available actions with examples."""
    try:
        executor = get_action_executor()
        actions = executor.get_available_actions()
        return [AvailableAction(**a) for a in actions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-log")
async def get_audit_log(limit: int = 50):
    """Get the action audit log."""
    try:
        executor = get_action_executor()
        log = executor.get_audit_log()
        return log[-limit:]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
