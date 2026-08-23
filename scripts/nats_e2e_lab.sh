#!/usr/bin/env bash
# BEL-207: NATS lab consumer E2E (docker nats + nats-py).
# Skips cleanly (exit 0) if docker/nats-py unavailable — CI default stays green.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=.
export ASPEN_SIM=1
export ASPEN_NATS_URL="${ASPEN_NATS_URL:-nats://127.0.0.1:4222}"

if ! command -v docker >/dev/null 2>&1; then
  echo "nats_e2e skip: docker not available"
  exit 0
fi

if ! python3 -c 'import nats' 2>/dev/null; then
  python3 -m pip install --user -q nats-py 2>/dev/null || python3 -m pip install -q nats-py 2>/dev/null || {
    echo "nats_e2e skip: cannot install nats-py"
    exit 0
  }
fi

NAME="aspen-lgw-nats-e2e-$$"
cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" -p 127.0.0.1:4222:4222 nats:2-alpine >/dev/null

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
    echo "nats_e2e skip: broker never became ready"
    exit 0
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
echo "nats_e2e ok"
