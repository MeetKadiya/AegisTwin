import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery

try:
    from .database.neo4j_client import graph_engine
    from .database.seed_topology import seed_database
    from .routers import topology, simulation, remediation
    from .agents.red_team_agent import red_team_agent
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from database.seed_topology import seed_database
    from routers import topology, simulation, remediation
    from agents.red_team_agent import red_team_agent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery app configuration for background distributed simulations
celery_app = Celery("aegistwin_simulations", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="tasks.run_threat_simulation")
def celery_run_threat_simulation(max_steps: int = 10):
    """Celery background task for long-running adversary simulations."""
    return red_team_agent.run_full_simulation(max_steps=max_steps)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Cyber Attack Digital Twin backend...")
    # Seed graph topology automatically on startup
    seed_database()
    logger.info("Topology initialized and ready.")
    yield
    logger.info("Shutting down backend and closing database connections...")
    graph_engine.close()


app = FastAPI(
    title="AI Cyber Attack Digital Twin Platform API",
    description="Autonomous red-team attack path simulation, MITRE ATT&CK mapping, and blast-radius modeling.",
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

# Register endpoints
app.include_router(topology.router)
app.include_router(simulation.router)
app.include_router(remediation.router)


@app.get("/")
def root():
    return {
        "service": "AI Cyber Attack Digital Twin Engine",
        "status": "OPERATIONAL",
        "neo4j_connected": graph_engine.is_neo4j_connected,
        "docs_url": "/docs"
    }


@app.get("/health")
def health_check():
    topo = graph_engine.get_topology()
    return {
        "status": "healthy",
        "neo4j_connected": graph_engine.is_neo4j_connected,
        "node_count": len(topo["nodes"]),
        "edge_count": len(topo["edges"])
    }
