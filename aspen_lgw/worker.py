"""Job consumer: aspen.worker.langgraph.job → graph → propose_act + result."""
from __future__ import annotations
import os
from typing import Any
from aspen_lgw.bus import LabBus
from aspen_lgw.propose import emit_propose_act, ProposeAct
from aspen_lgw.graphs.alarm_triage import build_alarm_triage_graph
from aspen_lgw.graphs.doc_assist import build_doc_assist_graph

GRAPHS = {
    "alarm_triage": "alarm",
    "doc_assist": "doc",
}


class LangGraphWorker:
    def __init__(self, bus: LabBus | None = None, node_id: str = "edge-sim-1", use_langgraph: bool | None = None):
        self.bus = bus or LabBus()
        self.node_id = node_id
        self.use_langgraph = (
            use_langgraph
            if use_langgraph is not None
            else os.environ.get("ASPEN_USE_LANGGRAPH", "0") == "1"
        )
        self.bus.subscribe("aspen.worker.langgraph.job", self._on_job)

    def _on_job(self, env: dict) -> None:
        self.handle_job(env.get("data") or {})

    def handle_job(self, job: dict[str, Any]) -> dict:
        job_id = job.get("id") or job.get("job_id") or "job"
        name = job.get("graph") or "alarm_triage"
        try:
            state, proposal = self._run_graph(name, job)
        except Exception as e:
            err = {"job_id": job_id, "graph": name, "ok": False, "error": str(e)}
            self.bus.publish("aspen.worker.langgraph.result", err, source="aspen-lgw")
            return err

        assert isinstance(proposal, ProposeAct)
        prop_env = emit_propose_act(self.bus, self.node_id, proposal, job_id=str(job_id))
        result = {
            "job_id": job_id,
            "graph": name,
            "ok": True,
            "trace": state.get("_trace"),
            "proposal_skill": proposal.skill,
            "propose_subject": prop_env["subject"],
            "backend": state.get("_backend", "stdlib"),
        }
        self.bus.publish("aspen.worker.langgraph.result", result, source="aspen-lgw")
        return result

    def _run_graph(self, name: str, job: dict) -> tuple[dict, ProposeAct]:
        if name == "alarm_triage":
            alarm = job.get("alarm") or job.get("input") or {}
            if self.use_langgraph:
                from aspen_lgw.optional_langgraph import langgraph_available, run_alarm_langgraph
                if langgraph_available():
                    state = run_alarm_langgraph(alarm)
                    state["_backend"] = "langgraph"
                    return state, state["proposal"]
            g = build_alarm_triage_graph()
            state = g.run({"alarm": alarm})
            state["_backend"] = "stdlib"
            return state, state["proposal"]

        if name == "doc_assist":
            g = build_doc_assist_graph()
            state = g.run({"query": job.get("query") or job.get("input") or ""})
            state["_backend"] = "stdlib"
            return state, state["proposal"]

        raise KeyError(f"unknown graph: {name}")
