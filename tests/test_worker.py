import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
from aspen_lgw import LabBus, LangGraphWorker

class TestWorker(unittest.TestCase):
    def test_job_alarm(self):
        bus = LabBus()
        w = LangGraphWorker(bus=bus)
        r = w.handle_job({"id": "1", "graph": "alarm_triage", "alarm": {"code": "A", "severity": "low", "message": "ping"}})
        self.assertTrue(r["ok"])
        self.assertEqual(r["proposal_skill"], "notify_operator")

    def test_doc_assist(self):
        bus = LabBus()
        w = LangGraphWorker(bus=bus)
        r = w.handle_job({"id": "2", "graph": "doc_assist", "query": "handoff shift"})
        self.assertTrue(r["ok"])

    def test_unknown_graph(self):
        bus = LabBus()
        w = LangGraphWorker(bus=bus)
        r = w.handle_job({"id": "3", "graph": "nope"})
        self.assertFalse(r["ok"])

if __name__ == "__main__":
    unittest.main()
