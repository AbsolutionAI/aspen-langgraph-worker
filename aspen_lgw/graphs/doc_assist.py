"""Tiny doc-assist graph: retrieve snippet → propose operator note (no act hardware)."""
from __future__ import annotations

from aspen_lgw.graph import StdlibGraph, GraphState
from aspen_lgw.propose import ProposeAct
from aspen_lgw.retrieval import Retriever, default_retriever


def build_doc_assist_graph(retriever: Retriever | None = None) -> StdlibGraph:
    ret = retriever or default_retriever()
    g = StdlibGraph(entry="retrieve")

    def retrieve(s: GraphState) -> GraphState:
        q = s.get("query") or ""
        hits = ret.search(str(q), k=3)
        s["hits"] = [{"id": h.id, "text": h.text, "score": h.score} for h in hits]
        s["_retriever"] = type(ret).__name__
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
