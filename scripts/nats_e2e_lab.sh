#!/usr/bin/env bash
# BEL-207: NATS lab consumer E2E (docker nats + nats-py).
# Skips cleanly (exit 0) if docker/nats-py unavailable — CI default stays green.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=.
export ASPEN_SIM=1
export ASPEN_NATS_URL="${ASPEN_NATS_URL:-nats://127.0.0.1:4222}"

# NATS_E2E_REQUIRED=1 (CI) turns every "skip" into a failure so the job can't
# go green without actually exercising the broker.
skip() {
  echo "nats_e2e skip: $*"
  if [[ "${NATS_E2E_REQUIRED:-0}" == "1" ]]; then
    echo "nats_e2e FAIL: NATS_E2E_REQUIRED=1 and the e2e was skipped" >&2
    exit 1
  fi
  exit 0
}

# Broker: a local nats-server binary (NATS_SERVER_BIN or PATH) is preferred;
# otherwise docker nats:2-alpine.
NATS_BIN="${NATS_SERVER_BIN:-$(command -v nats-server || true)}"
if [[ -z "$NATS_BIN" ]] && ! command -v docker >/dev/null 2>&1; then
  skip "neither nats-server nor docker available"
fi

if ! python3 -c 'import nats' 2>/dev/null; then
  python3 -m pip install --user -q nats-py 2>/dev/null || python3 -m pip install -q nats-py 2>/dev/null || {
    skip "cannot install nats-py"
  }
fi

NAME="aspen-lgw-nats-e2e-$$"
BROKER_PID=""
cleanup() {
  if [[ -n "$BROKER_PID" ]]; then
    kill "$BROKER_PID" >/dev/null 2>&1 || true
  else
    docker rm -f "$NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

PORT="${ASPEN_NATS_URL##*:}"
if [[ -n "$NATS_BIN" ]]; then
  echo "nats_e2e broker: $NATS_BIN (-js, 127.0.0.1:$PORT)"
  "$NATS_BIN" -a 127.0.0.1 -p "$PORT" -js -sd "$(mktemp -d)" >/dev/null 2>&1 &
  BROKER_PID=$!
else
  echo "nats_e2e broker: docker nats:2-alpine"
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker run -d --name "$NAME" -p "127.0.0.1:$PORT:4222" nats:2-alpine -js >/dev/null
fi

# wait for port
for i in $(seq 1 30); do
  if python3 - <<'PY'
import asyncio, os, sys
async def main():
    import nats
    try:
        nc = await asyncio.wait_for(nats.connect(os.environ["ASPEN_NATS_URL"]), timeout=0.4)
        await nc.drain()
        sys.exit(0)
    except Exception:
        sys.exit(1)
asyncio.run(main())
PY
  then
    break
  fi
  sleep 0.2
  if [[ "$i" -eq 30 ]]; then
    skip "broker never became ready"
  fi
done

# consumer in background (once mode waits for first job)
python3 - <<'PY' &
import asyncio, os
os.environ["ASPEN_NATS_ONCE"] = "1"
os.environ["ASPEN_NATS_IDLE_SECONDS"] = "8"
from aspen_lgw.nats_consumer import run_nats_consumer
raise SystemExit(asyncio.run(run_nats_consumer(idle_seconds=8, once=True)))
PY
CID=$!
sleep 0.4

# publish job via request
python3 - <<'PY'
import asyncio, json, os, sys
async def main():
    import nats
    nc = await nats.connect(os.environ["ASPEN_NATS_URL"])
    job = {
        "specversion": "1.0",
        "type": "aspen.worker.langgraph.job",
        "source": "nats-e2e",
        "subject": "aspen.worker.langgraph.job",
        "data": {
            "id": "e2e-1",
            "graph": "alarm_triage",
            "alarm": {"code": "E2E", "severity": "critical", "message": "estop"},
        },
    }
    msg = await nc.request("aspen.worker.langgraph.job", json.dumps(job).encode(), timeout=5)
    body = json.loads(msg.data.decode())
    data = body.get("data", body)
    print("nats_e2e result", json.dumps(data))
    assert data.get("ok") is True, data
    assert data.get("proposal_skill") == "hold_cell", data
    assert data.get("job_id") == "e2e-1", data
    await nc.drain()
asyncio.run(main())
PY

wait "$CID" || true

# JetStream lab check: the broker runs with -js; capture the result subject in
# a stream and replay one job so the result is durably stored (BEL-207 asks
# for a JetStream/lab broker smoke, not just core request/reply).
python3 - <<'PY' &
import asyncio, os
os.environ["ASPEN_NATS_ONCE"] = "1"
from aspen_lgw.nats_consumer import run_nats_consumer
raise SystemExit(asyncio.run(run_nats_consumer(idle_seconds=8, once=True)))
PY
CID=$!
sleep 0.4
python3 - <<'PY'
import asyncio, json, os
async def main():
    import nats
    nc = await nats.connect(os.environ["ASPEN_NATS_URL"])
    js = nc.jetstream()
    await js.add_stream(name="ASPEN_LGW_E2E", subjects=["aspen.worker.langgraph.result"])
    job = {"specversion": "1.0", "type": "aspen.worker.langgraph.job",
           "source": "nats-e2e", "subject": "aspen.worker.langgraph.job",
           "data": {"id": "e2e-js-1", "graph": "alarm_triage",
                    "alarm": {"code": "E2E", "severity": "critical", "message": "estop"}}}
    await nc.request("aspen.worker.langgraph.job", json.dumps(job).encode(), timeout=5)
    for _ in range(40):
        info = await js.stream_info("ASPEN_LGW_E2E")
        if info.state.messages >= 1:
            break
        await asyncio.sleep(0.1)
    assert info.state.messages >= 1, "result not captured by JetStream"
    msg = await js.get_last_msg("ASPEN_LGW_E2E", "aspen.worker.langgraph.result")
    body = json.loads(msg.data.decode())
    data = body.get("data", body)
    assert data.get("job_id") == "e2e-js-1", data
    print("nats_e2e jetstream result stored", json.dumps({"job_id": data.get("job_id")}))
    await nc.drain()
asyncio.run(main())
PY
wait "$CID" || true
echo "nats_e2e ok"
