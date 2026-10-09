from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

try:
    from ..agents.red_team_agent import red_team_agent
    from ..database.neo4j_client import graph_engine
    from ..streaming.websocket_hub import ws_hub
except (ImportError, ValueError):
    from agents.red_team_agent import red_team_agent
    from database.neo4j_client import graph_engine
    from streaming.websocket_hub import ws_hub


router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


class SimulationStartRequest(BaseModel):
    max_steps: Optional[int] = 10
    mode: Optional[str] = "autonomous"  # 'autonomous' or 'step_by_step'


@router.post("/start")
async def start_simulation(req: SimulationStartRequest):
    """
    Initiates the autonomous Red Team adversary simulation.
    Maps attack paths through Neo4j graph nodes and attributes MITRE ATT&CK TTPs.
    """
    result = red_team_agent.run_full_simulation(max_steps=req.max_steps or 10)
    topology = graph_engine.get_topology()
    await ws_hub.broadcast("topology", topology)
    return {
        "status": "COMPLETED",
        "result": result,
        "compromised_nodes": [n["id"] for n in topology["nodes"] if n.get("compromised")]
    }


@router.post("/step")
async def step_simulation():
    """Executes a single lateral movement or exploit step in the simulation."""
    result = red_team_agent.execute_next_step()
    topology = graph_engine.get_topology()
    await ws_hub.broadcast("topology", topology)
    if result.get("step"):
        await ws_hub.broadcast("alerts", result["step"])
    return result


@router.post("/reset")
async def reset_simulation():
    """Resets the simulation state and cleans compromise flags across all nodes."""
    red_team_agent.reset()
    topology = graph_engine.get_topology()
    await ws_hub.broadcast("topology", topology)
    return {
        "status": "RESET",
        "message": "All node compromise flags reset to clean baseline."
    }


@router.get("/history")
def get_simulation_history():
    """Returns the full historical attack path steps and MITRE ATT&CK breakdown."""
    history = red_team_agent.simulation_history
    tactics_count: Dict[str, int] = {}
    techniques_count: Dict[str, int] = {}

    for step in history:
        tactic = step.get("tactic", "Unknown")
        tactics_count[tactic] = tactics_count.get(tactic, 0) + 1
        tech = f"{step.get('technique_id')} - {step.get('technique_name')}"
        techniques_count[tech] = techniques_count.get(tech, 0) + 1

    return {
        "total_steps": len(history),
        "steps": history,
        "tactics_breakdown": tactics_count,
        "techniques_breakdown": techniques_count
    }
