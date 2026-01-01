"""
NEXUS Text-to-SQL API Server
=============================
A simple FastAPI server to run the NEXUS pipeline.

Usage:
    # Start the server
    python -m api.server
    
    # Or with uvicorn directly
    uvicorn api.server:app --reload --port 8000

API Endpoints:
    POST /query          - Run a natural language query
    POST /query/batch    - Run multiple queries
    GET  /health         - Health check
    GET  /schema         - Get database schema info
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time

from nexus_sql import create_pipeline, NexusPipeline
from database.connection import db_manager
from database.schema_manager import schema_manager

# Initialize FastAPI app
app = FastAPI(
    title="NEXUS Text-to-SQL API",
    description="Convert natural language questions to SQL queries for clinical trial data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (initialized on first request)
_pipeline: Optional[NexusPipeline] = None


def get_pipeline() -> NexusPipeline:
    """Get or create the pipeline instance"""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_pipeline(verbose=False)
    return _pipeline


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    question: str = Field(..., description="Natural language question to convert to SQL")
    num_candidates: int = Field(default=3, ge=1, le=10, description="Number of SQL candidates to generate")
    num_unit_tests: int = Field(default=5, ge=1, le=20, description="Number of unit tests to generate for candidate selection")
    disable_unit_test: bool = Field(default=False, description="Disable unit testing agent (faster but less accurate)")
    execute: bool = Field(default=True, description="Whether to execute the generated SQL")
    explain: bool = Field(default=True, description="Whether to generate natural language explanation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How many studies are there in the database?",
                "num_candidates": 3,
                "num_unit_tests": 5,
                "disable_unit_test": False,
                "execute": True,
                "explain": True
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    success: bool
    question: str
    sql: str
    explanation: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any]
    error: Optional[str] = None


class BatchQueryRequest(BaseModel):
    """Request model for batch query endpoint"""
    questions: List[str] = Field(..., description="List of questions to process")
    num_unit_tests: int = Field(default=5, ge=1, le=20, description="Number of unit tests per query")
    disable_unit_test: bool = Field(default=False, description="Disable unit testing for faster batch processing")
    execute: bool = Field(default=True)
    explain: bool = Field(default=False)


class BatchQueryResponse(BaseModel):
    """Response model for batch query endpoint"""
    results: List[QueryResponse]
    total_time: float
    success_count: int
    failure_count: int


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    database_connected: bool
    pipeline_ready: bool


class SchemaResponse(BaseModel):
    """Response model for schema endpoint"""
    tables: List[str]
    schema_details: Dict[str, Any]


# API Endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health and component status"""
    db_connected = False
    pipeline_ready = False
    
    try:
        # Check database connection
        db_manager.execute_query("SELECT 1")
        db_connected = True
    except Exception:
        pass
    
    try:
        # Check if pipeline can be created
        get_pipeline()
        pipeline_ready = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if db_connected and pipeline_ready else "degraded",
        database_connected=db_connected,
        pipeline_ready=pipeline_ready
    )


@app.get("/schema", response_model=SchemaResponse, tags=["Database"])
async def get_schema():
    """Get database schema information"""
    try:
        schema = schema_manager.get_schema()
        tables = list(schema.keys()) if schema else []
        
        return SchemaResponse(
            tables=tables,
            schema_details=schema or {}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def run_query(request: QueryRequest):
    """
    Convert a natural language question to SQL and optionally execute it.
    
    - **question**: The natural language question to convert
    - **num_candidates**: Number of SQL candidates to generate (1-10)
    - **num_unit_tests**: Number of unit tests to generate for candidate selection (1-20)
    - **disable_unit_test**: Skip unit testing agent for faster results
    - **execute**: Whether to execute the generated SQL
    - **explain**: Whether to generate natural language explanation
    """
    start_time = time.time()
    
    try:
        pipeline = get_pipeline()
        
        result = pipeline.run(
            question=request.question,
            num_candidates=request.num_candidates,
            num_unit_tests=request.num_unit_tests,
            disable_unit_test=request.disable_unit_test,
            execute_result=request.execute,
            explain_result=request.explain
        )
        
        total_time = time.time() - start_time
        
        return QueryResponse(
            success=result.success,
            question=request.question,
            sql=result.sql or "",
            explanation=result.explanation,
            execution_result=result.execution_result,
            metrics={
                "total_time": round(total_time, 2),
                "total_tokens": result.total_tokens,
                "pipeline_time": round(result.total_time, 2)
            },
            error=result.error
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            question=request.question,
            sql="",
            metrics={"total_time": round(time.time() - start_time, 2)},
            error=str(e)
        )


@app.post("/query/batch", response_model=BatchQueryResponse, tags=["Query"])
async def run_batch_query(request: BatchQueryRequest):
    """
    Process multiple questions in batch.
    
    - **questions**: List of natural language questions
    - **num_unit_tests**: Number of unit tests per query
    - **disable_unit_test**: Skip unit testing for faster batch processing
    - **execute**: Whether to execute generated SQL
    - **explain**: Whether to generate explanations (disabled by default for speed)
    """
    start_time = time.time()
    results = []
    success_count = 0
    
    pipeline = get_pipeline()
    
    for question in request.questions:
        q_start = time.time()
        try:
            result = pipeline.run(
                question=question,
                num_candidates=3,
                num_unit_tests=request.num_unit_tests,
                disable_unit_test=request.disable_unit_test,
                execute_result=request.execute,
                explain_result=request.explain
            )
            
            response = QueryResponse(
                success=result.success,
                question=question,
                sql=result.sql or "",
                explanation=result.explanation,
                execution_result=result.execution_result,
                metrics={
                    "total_time": round(time.time() - q_start, 2),
                    "total_tokens": result.total_tokens
                },
                error=result.error
            )
            
            if result.success:
                success_count += 1
                
        except Exception as e:
            response = QueryResponse(
                success=False,
                question=question,
                sql="",
                metrics={"total_time": round(time.time() - q_start, 2)},
                error=str(e)
            )
        
        results.append(response)
    
    return BatchQueryResponse(
        results=results,
        total_time=round(time.time() - start_time, 2),
        success_count=success_count,
        failure_count=len(request.questions) - success_count
    )


@app.get("/", tags=["System"])
async def root():
    """API root - returns basic info"""
    return {
        "name": "NEXUS Text-to-SQL API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
