# aspen-langgraph-worker

**License:** Apache-2.0  
**ADR:** [ADR-0005](https://github.com/AbsolutionAI/AspenOS/blob/main/docs/adr/ADR-0005-langgraph-execution-plugin.md)  
**SoR:** AspenGrove Master Spec v4.0

LangGraph-style **cognitive execution plugin** for AspenOS.  
**Paperclip remains the aspen-dev org runtime** — this package does not replace companies, budgets, or Hermes personas.

## Guarantees
- Safety-adjacent outputs are **`propose_act` only** (no drivers/actuators)
- Works offline in lab with in-process bus
- Core smoke uses a **stdlib graph runner**; optional `langgraph` extra later

## Quickstart
```bash
export PYTHONPATH=.
make smoke
python3 examples/alarm_triage_sim.py
```

## Not this package
- Paperclip boards / hiring / freeze budgets  
- Swarm mission scheduling (see aspen-swarm-manager)  
- Edge RRM lifecycle (see aspen-edge-rrm)
