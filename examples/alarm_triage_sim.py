import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"

from aspen_lgw import LabBus, build_alarm_triage_graph, emit_propose_act

bus = LabBus()
g = build_alarm_triage_graph()
state = g.run({"alarm": {"code": "E-STOP", "severity": "critical", "message": "estop pressed cell 2"}})
assert state["class"] == "safety_stop"
prop = state["proposal"]
assert prop.skill == "hold_cell"
assert prop.requires_dual_auth is True
env = emit_propose_act(bus, "edge-sim-1", prop, job_id="alarm-1")
assert env["subject"].endswith("propose_act")
assert env["data"]["direct_act_forbidden"] is True
# ensure we never published a raw act subject
assert not any(e["subject"].endswith(".act") for e in bus.history)
print("alarm_triage_sim ok", env["data"]["skill"], env["data"]["risk"])
print("trace", state["_trace"])
