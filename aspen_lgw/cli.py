def main():
    import json, os, argparse
    os.environ.setdefault("ASPEN_SIM", "1")
    p = argparse.ArgumentParser()
    p.add_argument("--graph", default="alarm_triage")
    p.add_argument("--langgraph", action="store_true")
    args = p.parse_args()
    from aspen_lgw import LabBus, LangGraphWorker
    bus = LabBus()
    w = LangGraphWorker(bus=bus, use_langgraph=args.langgraph)
    if args.graph == "doc_assist":
        job = {"id": "cli", "graph": "doc_assist", "query": "estop"}
    else:
        job = {"id": "cli", "graph": "alarm_triage", "alarm": {"code": "T-01", "severity": "high", "message": "overheat zone 3"}}
    print(json.dumps(w.handle_job(job), indent=2, default=str))

if __name__ == "__main__":
    main()
