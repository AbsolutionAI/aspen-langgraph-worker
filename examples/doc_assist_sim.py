import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw import LabBus, LangGraphWorker

bus = LabBus()
w = LangGraphWorker(bus=bus, node_id="edge-sim-1")
r = w.handle_job({"id": "d1", "graph": "doc_assist", "query": "estop resume procedure"})
assert r["ok"] and r["proposal_skill"] == "notify_operator"
assert any("propose_act" in e["subject"] for e in bus.history)
print("doc_assist_sim ok", r)
