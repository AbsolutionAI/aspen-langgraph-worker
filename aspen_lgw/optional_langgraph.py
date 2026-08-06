"""Optional real LangGraph backend. Falls back if not installed."""
from __future__ import annotations
from typing import Any, TypedDict, NotRequired

def langgraph_available() -> bool:
    try:
        from langgraph.graph import StateGraph  # noqa: F401
        return True
    except Exception:
        return False


class AlarmState(TypedDict):
    alarm: dict
    severity: NotRequired[str]
    code: NotRequired[str]
    message: NotRequired[str]
    class_: NotRequired[str]  # 'class' reserved-ish
    proposal: NotRequired[Any]
    _trace: NotRequired[list]


def build_alarm_triage_langgraph():
    """Return compiled LangGraph app or raise ImportError."""
    from langgraph.graph import StateGraph, START, END
    from aspen_lgw.propose import ProposeAct

    def ingest(s: AlarmState) -> dict:
        alarm = s.get("alarm") or {}
        return {
            "severity": str(alarm.get("severity", "medium")).lower(),
            "code": alarm.get("code", "UNKNOWN"),
            "message": alarm.get("message", ""),
            "_trace": (s.get("_trace") or []) + ["ingest"],
        }

    def classify(s: AlarmState) -> dict:
        msg = (s.get("message") or "").lower()
        sev = s.get("severity") or "medium"
        if "estop" in msg or sev == "critical":
            cls = "safety_stop"
        elif "temp" in msg or "overheat" in msg:
            cls = "thermal"
        else:
            cls = "generic"
        return {"class_": cls, "_trace": (s.get("_trace") or []) + ["classify"]}

    def plan(s: AlarmState) -> dict:
        cls = s.get("class_") or "generic"
        code = s.get("code")
        if cls == "safety_stop":
            prop = ProposeAct(
                skill="hold_cell",
                args={"reason": "safety_alarm", "code": code},
                reason="Critical/estop-class alarm — propose hold",
                risk="critical",
                requires_dual_auth=True,
            )
        elif cls == "thermal":
            prop = ProposeAct(
                skill="reduce_duty_cycle",
                args={"percent": 50, "code": code},
                reason="Thermal alarm — propose duty reduction",
                risk="high",
                requires_dual_auth=True,
            )
        else:
            prop = ProposeAct(
                skill="notify_operator",
                args={"code": code, "message": s.get("message")},
                reason="Generic alarm — notify only",
                risk="low",
                requires_dual_auth=False,
            )
        return {"proposal": prop, "_trace": (s.get("_trace") or []) + ["plan"]}

    g = StateGraph(AlarmState)
    g.add_node("ingest", ingest)
    g.add_node("classify", classify)
    g.add_node("plan", plan)
    g.add_edge(START, "ingest")
    g.add_edge("ingest", "classify")
    g.add_edge("classify", "plan")
    g.add_edge("plan", END)
    return g.compile()


def run_alarm_langgraph(alarm: dict) -> dict:
    app = build_alarm_triage_langgraph()
    out = app.invoke({"alarm": alarm, "_trace": []})
    # normalize class_ → class for callers
    if "class_" in out:
        out = dict(out)
        out["class"] = out.pop("class_")
    return out
