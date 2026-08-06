import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw.optional_langgraph import langgraph_available

class TestOptLG(unittest.TestCase):
    def test_optional(self):
        if not langgraph_available():
            self.skipTest("langgraph not installed")
        from aspen_lgw import LabBus, LangGraphWorker
        bus = LabBus()
        w = LangGraphWorker(bus=bus, use_langgraph=True)
        r = w.handle_job({"id": "x", "graph": "alarm_triage", "alarm": {"code": "E", "severity": "critical", "message": "estop"}})
        self.assertEqual(r.get("backend"), "langgraph")
        self.assertEqual(r["proposal_skill"], "hold_cell")

if __name__ == "__main__":
    unittest.main()
