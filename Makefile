.PHONY: smoke test
export PYTHONPATH := .
test:
	@python3 -m unittest tests.test_alarm_triage tests.test_worker tests.test_optional_langgraph -v
smoke: test
	@PYTHONPATH=. python3 examples/alarm_triage_sim.py
	@PYTHONPATH=. python3 examples/doc_assist_sim.py
	@PYTHONPATH=. python3 examples/worker_job_bus.py
	@PYTHONPATH=. python3 examples/langgraph_backend_sim.py
	@PYTHONPATH=. python3 examples/nats_consumer_once.py
	@echo aspen-langgraph-worker smoke ok
