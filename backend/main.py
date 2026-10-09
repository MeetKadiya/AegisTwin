import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .database.neo4j_client import graph_engine
    from .database.seed_topology import seed_database
    from .routers import topology, simulation, remediation, streaming, auth, tenants, integrations, compliance
    from .streaming.nats_consumer import nats_consumer
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from database.seed_topology import seed_database
    from routers import topology, simulation, remediation, streaming, auth, tenants, integrations, compliance
    from streaming.nats_consumer import nats_consumer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Cyber Attack Digital Twin backend...")
    # Seed graph topology automatically on startup
    seed_database()
    logger.info("Topology initialized and ready.")

    # Start background NATS JetStream edge telemetry consumer
    await nats_consumer.start()
    logger.info("NATS Telemetry Consumer started.")

    yield

    logger.info("Shutting down backend and closing database connections...")
    await nats_consumer.stop()
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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(topology.router)
app.include_router(simulation.router)
app.include_router(remediation.router)
app.include_router(streaming.router)
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(integrations.router)
app.include_router(compliance.router)


@app.get("/")
def root():
    return {
        "service": "AI Cyber Attack Digital Twin Engine",
        "status": "OPERATIONAL",
        "neo4j_connected": graph_engine.is_neo4j_connected,
        "docs_url": "/docs"
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "neo4j_connected": graph_engine.is_neo4j_connected
    }
