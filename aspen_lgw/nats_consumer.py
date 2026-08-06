"""Optional NATS job consumer — skips cleanly if no server/deps."""
from __future__ import annotations
import asyncio
import json
import logging
import os

logging.getLogger("nats").setLevel(logging.CRITICAL)


async def run_nats_consumer(node_id: str = "edge-sim-1") -> int:
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

    async def handler(msg):
        try:
            env = json.loads(msg.data.decode())
            data = env.get("data", env)
            worker.handle_job(data)
            # publish result events back (best-effort)
            for e in bus.history[-2:]:
                await nc.publish(e["subject"], json.dumps(e).encode())
        except Exception as ex:
            print("handler error", ex)

    await nc.subscribe("aspen.worker.langgraph.job", cb=handler)
    print("nats_consumer listening aspen.worker.langgraph.job")
    # lab: run briefly then exit if ASPEN_NATS_ONCE
    if os.environ.get("ASPEN_NATS_ONCE") == "1":
        await asyncio.sleep(0.5)
        await nc.drain()
        print("nats_consumer once exit")
        return 0
    while True:
        await asyncio.sleep(3600)


def main():
    raise SystemExit(asyncio.run(run_nats_consumer()))


if __name__ == "__main__":
    main()
