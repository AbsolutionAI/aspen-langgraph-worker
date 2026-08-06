import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw.optional_langgraph import langgraph_available

if not langgraph_available():
    print("langgraph_backend_sim skip: langgraph not installed")
    raise SystemExit(0)

from aspen_lgw import LabBus, LangGraphWorker
bus = LabBus()
w = LangGraphWorker(bus=bus, use_langgraph=True)
r = w.handle_job({
    "id": "lg-1",
    "graph": "alarm_triage",
    "alarm": {"code": "T9", "severity": "high", "message": "overheat motor"},
})
assert r["ok"] and r.get("backend") == "langgraph"
assert r["proposal_skill"] == "reduce_duty_cycle"
print("langgraph_backend_sim ok", r)
