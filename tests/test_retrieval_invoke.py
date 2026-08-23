import os, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_SIM"] = "1"
# ensure no accidental pgvector path in unit tests
os.environ.pop("ASPEN_PGVECTOR_DSN", None)

from aspen_lgw.retrieval import InMemoryRetriever, CascadingRetriever, default_retriever, DocHit
from aspen_lgw.graphs.doc_assist import build_doc_assist_graph
from aspen_lgw.invoke import build_job, invoke_lab


class TestRetrieval(unittest.TestCase):
    def test_memory_estop(self):
        r = InMemoryRetriever()
        hits = r.search("estop freeze")
        self.assertTrue(hits)
        self.assertEqual(hits[0].id, "sop-estop")

    def test_default_is_memory(self):
        self.assertIsInstance(default_retriever(), InMemoryRetriever)

    def test_cascade_falls_back(self):
        class Empty:
            def search(self, query, k=3):
                return []

        r = CascadingRetriever(primary=Empty(), fallback=InMemoryRetriever())
        hits = r.search("thermal overtemp")
        self.assertTrue(hits)
        self.assertEqual(hits[0].id, "sop-thermal")

    def test_doc_graph_uses_retriever(self):
        g = build_doc_assist_graph(InMemoryRetriever())
        state = g.run({"query": "handoff shift"})
        self.assertTrue(state.get("hits"))
        self.assertEqual(state["proposal"].skill, "notify_operator")


class TestInvoke(unittest.TestCase):
    def test_lab_alarm(self):
        job = build_job("alarm_triage", job_id="t-inv")
        out = invoke_lab(job)
        self.assertTrue(out["result"]["ok"])
        self.assertEqual(out["result"]["proposal_skill"], "hold_cell")
        self.assertGreaterEqual(out["propose_count"], 1)


if __name__ == "__main__":
    unittest.main()
