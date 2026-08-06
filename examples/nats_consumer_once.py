import os, sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ASPEN_NATS_ONCE"] = "1"
from aspen_lgw.nats_consumer import run_nats_consumer
raise SystemExit(asyncio.run(run_nats_consumer()))
