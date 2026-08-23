# aspen-langgraph-worker

**License:** Apache-2.0  
**Version:** 0.2.0  
**ADR:** [ADR-0005](https://github.com/AbsolutionAI/AspenOS/blob/main/docs/adr/ADR-0005-langgraph-execution-plugin.md)  
**SoR:** AspenGrove Master Spec v4.0  
**Paperclip:** ASP-66 · Linear epic BEL-200

LangGraph-style **cognitive execution plugin** for AspenOS.  
**Paperclip remains the aspen-dev org runtime** — this package does not replace companies, budgets, or Hermes personas.

## Guarantees
- Safety-adjacent outputs are **`propose_act` only** (`direct_act_forbidden: true`)
- Works offline in lab with in-process bus
- Core smoke uses a **stdlib graph runner**; optional `langgraph` / `nats` / `pgvector` extras
- Never schedules swarm missions or hires Paperclip agents

## Quickstart
```bash
export PYTHONPATH=.
make smoke
python3 -m aspen_lgw.invoke --transport lab --graph alarm_triage
```

## Not this package
- Paperclip boards / hiring / freeze budgets  
- Swarm mission scheduling (see aspen-swarm-manager)  
- Edge RRM lifecycle (see aspen-edge-rrm)

## Graphs
| Name | Purpose |
|------|---------|
| `alarm_triage` | Classify plant alarm → propose_act |
| `doc_assist` | SOP retrieve (memory or optional pgvector) → notify_operator proposal |

## Job bus
Publish to `aspen.worker.langgraph.job`:
```json
{"id": "j1", "graph": "alarm_triage", "alarm": {"code": "E1", "severity": "critical", "message": "estop"}}
```
Results: `aspen.worker.langgraph.result` + `aspen.edge.<node>.propose_act`.

## Optional backends
```bash
pip install 'aspen-langgraph-worker[langgraph]'   # real StateGraph
pip install 'aspen-langgraph-worker[nats]'        # NATS consumer / invoke
pip install 'aspen-langgraph-worker[pgvector]'    # optional SOP DSN
export ASPEN_USE_LANGGRAPH=1
export ASPEN_NATS_URL=nats://127.0.0.1:4222
# export ASPEN_PGVECTOR_DSN=postgresql://...   # optional; memory fallback always works
```

## NATS lab E2E
```bash
make nats-e2e   # docker nats:2-alpine + request/reply; skips if docker/nats-py missing
```

## Hermes / Paperclip invoke
See [docs/INVOKE.md](docs/INVOKE.md).

## Compose
aspen-grove profile `langgraph` → `compose/langgraph-lab.yml` (NATS + worker consumer).
