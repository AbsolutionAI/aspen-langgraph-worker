from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .bus import LabBus

@dataclass
class ProposeAct:
    skill: str
    args: dict
    reason: str
    risk: str = "medium"  # low|medium|high|critical
    requires_dual_auth: bool = True

def emit_propose_act(bus: LabBus, node_id: str, proposal: ProposeAct, job_id: str | None = None) -> dict:
    """ONLY legal act-shaped output from this worker."""
    data = {
        "skill": proposal.skill,
        "args": proposal.args,
        "reason": proposal.reason,
        "risk": proposal.risk,
        "requires_dual_auth": proposal.requires_dual_auth,
        "agent": "langgraph-worker",
        "job_id": job_id,
        "direct_act_forbidden": True,
    }
    return bus.publish(f"aspen.edge.{node_id}.propose_act", data, source="aspen-lgw")
