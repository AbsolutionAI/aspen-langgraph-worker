import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw import LabBus, LangGraphWorker

bus = LabBus()
w = LangGraphWorker(bus=bus)
# publish job on bus (as external caller would)
bus.publish("aspen.worker.langgraph.job", {
    "id": "j-bus-1",
    "graph": "alarm_triage",
    "alarm": {"code": "E1", "severity": "critical", "message": "estop"},
})
results = [e for e in bus.history if e["subject"] == "aspen.worker.langgraph.result"]
proposes = [e for e in bus.history if "propose_act" in e["subject"]]
assert results and results[-1]["data"]["ok"]
assert proposes and proposes[-1]["data"]["skill"] == "hold_cell"
print("worker_job_bus ok", results[-1]["data"])
