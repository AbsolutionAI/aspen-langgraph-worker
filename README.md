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

## Graphs
| Name | Purpose |
|------|---------|
| `alarm_triage` | Classify plant alarm → propose_act |
| `doc_assist` | Tiny SOP retrieve → notify_operator proposal |

## Job bus
Publish to `aspen.worker.langgraph.job`:
```json
{"id": "j1", "graph": "alarm_triage", "alarm": {"code": "E1", "severity": "critical", "message": "estop"}}
```
Results: `aspen.worker.langgraph.result` + `aspen.edge.<node>.propose_act`.

## Optional LangGraph
```bash
pip install 'aspen-langgraph-worker[langgraph]'
export ASPEN_USE_LANGGRAPH=1
```

## Optional NATS
```bash
pip install nats-py
export ASPEN_NATS_URL=nats://127.0.0.1:4222
python -m aspen_lgw.nats_consumer
```
