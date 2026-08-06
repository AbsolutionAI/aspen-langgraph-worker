"""Minimal LangGraph-shaped runner (stdlib). Optional real langgraph later."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

GraphState = dict[str, Any]
NodeFn = Callable[[GraphState], GraphState]

@dataclass
class StdlibGraph:
    nodes: dict[str, NodeFn] = field(default_factory=dict)
    edges: dict[str, str | Callable[[GraphState], str]] = field(default_factory=dict)
    entry: str = "start"

    def add_node(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn

    def add_edge(self, a: str, b: str | Callable[[GraphState], str]) -> None:
        self.edges[a] = b

    def run(self, state: GraphState, max_steps: int = 32) -> GraphState:
        cur = self.entry
        steps = 0
        state = dict(state)
        state.setdefault("_trace", [])
        while cur and cur != "END":
            if cur not in self.nodes:
                raise KeyError(f"unknown node {cur}")
            state = self.nodes[cur](state)
            state["_trace"].append(cur)
            steps += 1
            if steps > max_steps:
                raise RuntimeError("max_steps exceeded")
            nxt = self.edges.get(cur, "END")
            cur = nxt(state) if callable(nxt) else nxt
        return state
