"""API Module - FastAPI endpoints for SAGE-Flow platform."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Global instances initialized at startup
_sage_flow = None
_graph = None
_dqi_calculator = None
_alert_engine = None
_benchmark_engine = None
_ranking_engine = None
_report_generator = None
_action_executor = None


def initialize_all():
    """Initialize all SAGE-Flow components at startup."""
    global _sage_flow, _graph, _dqi_calculator, _alert_engine
    global _benchmark_engine, _ranking_engine, _report_generator, _action_executor
    
    print("🔮 Initializing SAGE-Flow Clinical Intelligence Platform...")
    
    # Initialize SAGE-Flow orchestrator
    from sage_flow import create_sage_flow
    _sage_flow = create_sage_flow(verbose=False)
    _graph = _sage_flow.graph_agent.graph
    print(f"✅ SAGE-Flow initialized with {_graph.number_of_nodes():,} nodes")
    
    # Initialize DQI Calculator
    from intelligence.dqi import DQICalculator
    _dqi_calculator = DQICalculator(_graph)
    print("✅ DQI Engine initialized")
    
    # Initialize Alert Engine
    from alerting import AlertEngine
    _alert_engine = AlertEngine(_graph, dqi_calculator=_dqi_calculator)
    print("✅ Alert Engine initialized")
    
    # Initialize Analytics
    from analytics import BenchmarkEngine, RankingEngine
    _benchmark_engine = BenchmarkEngine(_graph, _dqi_calculator)
    _ranking_engine = RankingEngine(_graph, _dqi_calculator)
    print("✅ Analytics Engine initialized")
    
    # Initialize Report Generator
    from reporting import ReportGenerator
    _report_generator = ReportGenerator(
        graph=_graph,
        dqi_calculator=_dqi_calculator,
        benchmark_engine=_benchmark_engine,
        ranking_engine=_ranking_engine,
        alert_engine=_alert_engine
    )
    print("✅ Report Generator initialized")
    
    # Initialize Action Executor
    from actions import ActionExecutor
    _action_executor = ActionExecutor(
        graph=_graph,
        report_generator=_report_generator,
        alert_engine=_alert_engine,
        dqi_calculator=_dqi_calculator
    )
    print("✅ Action Executor initialized")
    
    print("🚀 SAGE-Flow Platform Ready!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components on startup."""
    initialize_all()
    yield
    print("👋 SAGE-Flow shutting down...")


app = FastAPI(
    title="SAGE-Flow Clinical Intelligence API",
    description="SQL-Augmented Graph Execution Flow for Clinical Trials",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import query, dqi, alerts, reports, actions, analytics

app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(dqi.router, prefix="/api/dqi", tags=["DQI"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    return {
        "name": "SAGE-Flow Clinical Intelligence API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "query": "/api/query",
            "dqi": "/api/dqi",
            "alerts": "/api/alerts",
            "reports": "/api/reports",
            "actions": "/api/actions",
            "analytics": "/api/analytics"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
