def main():
    import json, os
    from aspen_lgw.bus import LabBus
    from aspen_lgw.propose import emit_propose_act
    from aspen_lgw.graphs.alarm_triage import build_alarm_triage_graph
    os.environ.setdefault("ASPEN_SIM", "1")
    bus = LabBus()
    g = build_alarm_triage_graph()
    state = g.run({"alarm": {"code": "T-01", "severity": "high", "message": "overheat zone 3"}})
    prop = state["proposal"]
    env = emit_propose_act(bus, "edge-sim-1", prop, job_id="cli-demo")
    print(json.dumps({"trace": state["_trace"], "propose": env["data"]}, indent=2))

if __name__ == "__main__":
    main()
