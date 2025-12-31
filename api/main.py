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
    
    print("🔮 Initializing SAGE-Code Clinical Intelligence Platform...")
    
    # Initialize SAGE-Code orchestrator
    try:
        from sage_code.agent import create_agent
        _sage_flow = create_agent(auto_load=True)
        _graph = _sage_flow.graph
        print(f"✅ SAGE-Code initialized with {_graph.number_of_nodes():,} nodes")
    except ImportError as e:
        print(f"⚠️ SAGE-Code not found/failed: {e}")
        
    # Initialize DQI Calculator
    try:
        from intelligence.dqi import DQICalculator
        if _graph:
            _dqi_calculator = DQICalculator(_graph)
            print("✅ DQI Engine initialized")
    except ImportError:
        print("⚠️ Legacy DQI Engine not found")
        
    # Initialize Alert Engine
    try:
        from alerting import AlertEngine
        if _graph and _dqi_calculator:
            _alert_engine = AlertEngine(_graph, dqi_calculator=_dqi_calculator)
            print("✅ Alert Engine initialized")
    except ImportError:
        print("⚠️ Alert Engine not found")
        
    # Initialize Analytics
    try:
        from analytics import BenchmarkEngine, RankingEngine
        if _graph and _dqi_calculator:
            _benchmark_engine = BenchmarkEngine(_graph, _dqi_calculator)
            _ranking_engine = RankingEngine(_graph, _dqi_calculator)
            print("✅ Analytics Engine initialized")
    except ImportError:
        print("⚠️ Analytics Engine not found")

    # Initialize Report Generator
    try:
        from reporting import ReportGenerator
        if _graph and _dqi_calculator:
            _report_generator = ReportGenerator(
                graph=_graph,
                dqi_calculator=_dqi_calculator,
                benchmark_engine=_benchmark_engine,
                ranking_engine=_ranking_engine,
                alert_engine=_alert_engine
            )
            print("✅ Report Generator initialized")
    except ImportError:
        print("⚠️ Report Generator not found")
        
    # Initialize Action Executor
    try:
        from actions import ActionExecutor
        if _graph and _report_generator:
            _action_executor = ActionExecutor(
                graph=_graph,
                report_generator=_report_generator,
                alert_engine=_alert_engine,
                dqi_calculator=_dqi_calculator
            )
            print("✅ Action Executor initialized")
    except ImportError:
        print("⚠️ Action Executor not found")
    
    print("🚀 SAGE-Code Platform Ready ")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components on startup."""
    initialize_all()
    yield
    print("👋 SAGE-Code shutting down...")


app = FastAPI(
    title="SAGE-Code Clinical Intelligence API",
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

from api.routes import query, dqi, alerts, reports, actions, analytics, risk, clustering

app.include_router(dqi.router, prefix="/api/dqi", tags=["DQI"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(clustering.router, prefix="/api/analytics/clustering", tags=["Clustering"])


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
