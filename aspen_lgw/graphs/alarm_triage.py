"""Alarm triage → propose_act (sim). Never actuates."""
from __future__ import annotations
from aspen_lgw.graph import StdlibGraph, GraphState
from aspen_lgw.propose import ProposeAct

def build_alarm_triage_graph() -> StdlibGraph:
    g = StdlibGraph(entry="ingest")

    def ingest(s: GraphState) -> GraphState:
        alarm = s.get("alarm") or {}
        s["severity"] = str(alarm.get("severity", "medium")).lower()
        s["code"] = alarm.get("code", "UNKNOWN")
        s["message"] = alarm.get("message", "")
        return s

    def classify(s: GraphState) -> GraphState:
        # trivial rules — replace with LLM/tool node when keys available
        msg = (s.get("message") or "").lower()
        if "estop" in msg or s["severity"] == "critical":
            s["class"] = "safety_stop"
        elif "temp" in msg or "overheat" in msg:
            s["class"] = "thermal"
        else:
            s["class"] = "generic"
        return s

    def plan(s: GraphState) -> GraphState:
        cls = s.get("class")
        if cls == "safety_stop":
            s["proposal"] = ProposeAct(
                skill="hold_cell",
                args={"reason": "safety_alarm", "code": s.get("code")},
                reason="Critical/estop-class alarm — propose hold, do not auto-clear",
                risk="critical",
                requires_dual_auth=True,
            )
        elif cls == "thermal":
            s["proposal"] = ProposeAct(
                skill="reduce_duty_cycle",
                args={"percent": 50, "code": s.get("code")},
                reason="Thermal alarm — propose duty reduction pending auth",
                risk="high",
                requires_dual_auth=True,
            )
        else:
            s["proposal"] = ProposeAct(
                skill="notify_operator",
                args={"code": s.get("code"), "message": s.get("message")},
                reason="Generic alarm — notify only",
                risk="low",
                requires_dual_auth=False,
            )
        return s

    g.add_node("ingest", ingest)
    g.add_node("classify", classify)
    g.add_node("plan", plan)
    g.add_edge("ingest", "classify")
    g.add_edge("classify", "plan")
    g.add_edge("plan", "END")
    return g
