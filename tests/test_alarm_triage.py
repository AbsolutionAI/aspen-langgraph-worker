import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw import LabBus, build_alarm_triage_graph, emit_propose_act

class TestAlarm(unittest.TestCase):
    def test_thermal_proposes_duty(self):
        g = build_alarm_triage_graph()
        s = g.run({"alarm": {"code": "T1", "severity": "high", "message": "temp high"}})
        self.assertEqual(s["proposal"].skill, "reduce_duty_cycle")

    def test_only_propose_act(self):
        bus = LabBus()
        g = build_alarm_triage_graph()
        s = g.run({"alarm": {"code": "X", "severity": "low", "message": "info"}})
        emit_propose_act(bus, "n1", s["proposal"])
        self.assertTrue(all("propose_act" in e["subject"] for e in bus.history))

if __name__ == "__main__":
    unittest.main()
