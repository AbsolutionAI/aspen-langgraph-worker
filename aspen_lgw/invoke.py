"""Hermes / Paperclip invoke path — publish a langgraph job (lab bus or NATS).

Safety: this only publishes jobs; worker still emits propose_act only.
Does NOT create Paperclip companies or schedule swarm missions.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any


def build_job(
    graph: str,
    *,
    job_id: str = "invoke-1",
    alarm: dict | None = None,
    query: str | None = None,
    extra: dict | None = None,
) -> dict[str, Any]:
    job: dict[str, Any] = {"id": job_id, "graph": graph}
    if graph == "doc_assist":
        job["query"] = query if query is not None else "estop"
    else:
        job["alarm"] = alarm or {
            "code": "INV-1",
            "severity": "critical",
            "message": "estop",
        }
    if extra:
        job.update(extra)
    return job


def invoke_lab(job: dict, node_id: str = "edge-sim-1") -> dict:
    from aspen_lgw.bus import LabBus
    from aspen_lgw.worker import LangGraphWorker

    bus = LabBus()
    w = LangGraphWorker(bus=bus, node_id=node_id)
    result = w.handle_job(job)
    proposes = [e for e in bus.history if str(e.get("subject", "")).endswith(".propose_act")]
    # hard safety check for invoke path
    for p in proposes:
        data = p.get("data") or {}
        if data.get("direct_act_forbidden") is not True:
            raise AssertionError("propose_act missing direct_act_forbidden")
    return {"result": result, "propose_count": len(proposes), "backend": "lab"}


async def invoke_nats(job: dict, *, url: str | None = None, timeout: float = 3.0) -> dict:
    try:
        import nats
    except ImportError as e:
        raise RuntimeError("nats-py not installed") from e

    nats_url = url or os.environ.get("ASPEN_NATS_URL", "nats://127.0.0.1:4222")
    nc = await asyncio.wait_for(nats.connect(nats_url), timeout=1.5)
    try:
        envelope = {
            "specversion": "1.0",
            "type": "aspen.worker.langgraph.job",
            "source": "aspen-lgw-invoke",
            "data": job,
            "subject": "aspen.worker.langgraph.job",
        }
        # request/reply if consumer supports reply; else fire-and-forget + short wait
        try:
            msg = await nc.request(
                "aspen.worker.langgraph.job",
                json.dumps(envelope).encode(),
                timeout=timeout,
            )
            body = json.loads(msg.data.decode())
            data = body.get("data", body)
            return {"result": data, "backend": "nats-request"}
        except Exception:
            await nc.publish("aspen.worker.langgraph.job", json.dumps(envelope).encode())
            await asyncio.sleep(0.3)
            return {"result": {"ok": True, "published": True, "job_id": job.get("id")}, "backend": "nats-publish"}
    finally:
        await nc.drain()


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("ASPEN_SIM", "1")
    p = argparse.ArgumentParser(description="Invoke aspen-langgraph-worker job (lab or NATS)")
    p.add_argument("--graph", default="alarm_triage", choices=["alarm_triage", "doc_assist"])
    p.add_argument("--job-id", default="invoke-1")
    p.add_argument("--query", default="estop handoff")
    p.add_argument("--node-id", default="edge-sim-1")
    p.add_argument("--transport", choices=["lab", "nats", "auto"], default="lab")
    p.add_argument("--nats-url", default=None)
    p.add_argument("--json-job", default=None, help="Raw job JSON string (overrides graph helpers)")
    args = p.parse_args(argv)

    if args.json_job:
        job = json.loads(args.json_job)
    else:
        job = build_job(args.graph, job_id=args.job_id, query=args.query)

    transport = args.transport
    if transport == "auto":
        transport = "nats" if os.environ.get("ASPEN_NATS_URL") else "lab"

    if transport == "lab":
        out = invoke_lab(job, node_id=args.node_id)
    else:
        out = asyncio.run(invoke_nats(job, url=args.nats_url))

    print(json.dumps(out, indent=2, default=str))
    ok = bool((out.get("result") or {}).get("ok", True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
