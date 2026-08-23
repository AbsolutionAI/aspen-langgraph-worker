# Hermes / Paperclip invoke → LangGraph worker

**Rule:** Paperclip stays **aspen-dev** org/cost SoR. This hook only publishes a **cognitive job**.  
Worker output is **`propose_act` only** (`direct_act_forbidden: true`).

## Lab (no NATS)

```bash
export PYTHONPATH=.
python3 -m aspen_lgw.invoke --transport lab --graph alarm_triage
python3 -m aspen_lgw.invoke --transport lab --graph doc_assist --query "thermal coolant"
```

## NATS lab

```bash
# terminal A — broker + consumer
docker run --rm -p 4222:4222 nats:2-alpine
pip install nats-py
python -m aspen_lgw.nats_consumer

# terminal B
export ASPEN_NATS_URL=nats://127.0.0.1:4222
python3 -m aspen_lgw.invoke --transport nats --graph alarm_triage
```

## Paperclip / Hermes agent pattern

From an agent heartbeat (AGENTS.md skill note):

1. Prefer **lab** transport inside CI/unit proofs.
2. For fleet lab compose profile `langgraph`, set `ASPEN_NATS_URL` and use `--transport nats`.
3. Never treat a successful job as **act** — only as a proposal for edge-rrm / dual-auth.
4. Do **not** hire LangGraph “company agents” or replace Paperclip boards.

Example Paperclip comment body after invoke:

```
Invoked aspen-langgraph-worker graph=alarm_triage job_id=… → propose_act skill=hold_cell (sim).
```

## Compose

See aspen-grove `compose/langgraph-lab.yml` (profile `langgraph`).
