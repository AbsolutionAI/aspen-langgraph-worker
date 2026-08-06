"""Tiny doc-assist graph: retrieve snippet → propose operator note (no act hardware)."""
from __future__ import annotations
from aspen_lgw.graph import StdlibGraph, GraphState
from aspen_lgw.propose import ProposeAct

# Lab corpus — replace with pgvector later
CORPUS = [
    {"id": "sop-estop", "text": "E-stop: freeze motion, notify lead, dual-auth before resume."},
    {"id": "sop-thermal", "text": "Overtemp: reduce duty cycle 50%, check coolant, log sensor id."},
    {"id": "sop-handoff", "text": "Shift handoff: write what changed, open alarms, safe defaults."},
]


def build_doc_assist_graph() -> StdlibGraph:
    g = StdlibGraph(entry="retrieve")

    def retrieve(s: GraphState) -> GraphState:
        q = (s.get("query") or "").lower()
        hits = []
        for doc in CORPUS:
            score = sum(1 for w in q.split() if w in doc["text"].lower())
            if score:
                hits.append((score, doc))
        hits.sort(key=lambda x: -x[0])
        s["hits"] = [h[1] for h in hits[:3]]
        return s

    def propose(s: GraphState) -> GraphState:
        hits = s.get("hits") or []
        if not hits:
            s["proposal"] = ProposeAct(
                skill="notify_operator",
                args={"message": "No SOP hit for query", "query": s.get("query")},
                reason="Doc assist miss",
                risk="low",
                requires_dual_auth=False,
            )
        else:
            top = hits[0]
            s["proposal"] = ProposeAct(
                skill="notify_operator",
                args={
                    "message": f"SOP {top['id']}: {top['text']}",
                    "query": s.get("query"),
                    "doc_id": top["id"],
                },
                reason="Doc assist retrieval — operator note only",
                risk="low",
                requires_dual_auth=False,
            )
        return s

    g.add_node("retrieve", retrieve)
    g.add_node("propose", propose)
    g.add_edge("retrieve", "propose")
    g.add_edge("propose", "END")
    return g
