"""Optional NATS job consumer — skips cleanly if no server/deps.

Subjects:
  in:  aspen.worker.langgraph.job
  out: aspen.worker.langgraph.result
       aspen.edge.<node>.propose_act
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

logging.getLogger("nats").setLevel(logging.CRITICAL)

JOB_SUBJECT = "aspen.worker.langgraph.job"
RESULT_SUBJECT = "aspen.worker.langgraph.result"


async def run_nats_consumer(
    node_id: str = "edge-sim-1",
    *,
    once: bool | None = None,
    idle_seconds: float | None = None,
) -> int:
    try:
        import nats
    except ImportError:
        print("nats_consumer skip: nats-py not installed")
        return 0

    url = os.environ.get("ASPEN_NATS_URL", "nats://127.0.0.1:4222")
    try:
        nc = await asyncio.wait_for(nats.connect(url), timeout=1.5)
    except Exception as e:
        print(f"nats_consumer skip: {type(e).__name__}")
        return 0

    from aspen_lgw.bus import LabBus
    from aspen_lgw.worker import LangGraphWorker

    bus = LabBus()
    worker = LangGraphWorker(bus=bus, node_id=node_id)
    jobs_done = 0

    async def handler(msg):
        nonlocal jobs_done
        try:
            env = json.loads(msg.data.decode())
            data = env.get("data", env)
            # drain prior bus noise for this job's reply pair
            before = len(bus.history)
            worker.handle_job(data)
            for e in bus.history[before:]:
                subj = e.get("subject") or e.get("type")
                await nc.publish(subj, json.dumps(e).encode())
            jobs_done += 1
            if msg.reply:
                # optional core NATS request/reply ack with last result
                last = next(
                    (x for x in reversed(bus.history) if x.get("subject") == RESULT_SUBJECT),
                    {"ok": True, "jobs_done": jobs_done},
                )
                await nc.publish(msg.reply, json.dumps(last).encode())
        except Exception as ex:
            print("handler error", ex)
            if msg.reply:
                await nc.publish(msg.reply, json.dumps({"ok": False, "error": str(ex)}).encode())

    await nc.subscribe(JOB_SUBJECT, cb=handler)
    print(f"nats_consumer listening {JOB_SUBJECT} node={node_id}")

    do_once = once if once is not None else os.environ.get("ASPEN_NATS_ONCE") == "1"
    idle = idle_seconds
    if idle is None:
        idle = float(os.environ.get("ASPEN_NATS_IDLE_SECONDS", "0.5" if do_once else "0"))

    if do_once:
        # wait until at least one job or idle timeout
        deadline = asyncio.get_event_loop().time() + max(idle, 0.1)
        while jobs_done == 0 and asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.05)
        # small drain window for publishes
        await asyncio.sleep(0.1)
        await nc.drain()
        print(f"nats_consumer once exit jobs_done={jobs_done}")
        return 0

    if idle and idle > 0:
        await asyncio.sleep(idle)
        await nc.drain()
        print(f"nats_consumer idle exit jobs_done={jobs_done}")
        return 0

    while True:
        await asyncio.sleep(3600)


def main():
    raise SystemExit(asyncio.run(run_nats_consumer()))


if __name__ == "__main__":
    main()
