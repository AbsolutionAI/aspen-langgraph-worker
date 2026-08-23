.PHONY: smoke test nats-e2e
export PYTHONPATH := .

test:
	@python3 -m unittest \
		tests.test_alarm_triage \
		tests.test_worker \
		tests.test_optional_langgraph \
		tests.test_retrieval_invoke \
		-v

smoke: test
	@PYTHONPATH=. python3 examples/alarm_triage_sim.py
	@PYTHONPATH=. python3 examples/doc_assist_sim.py
	@PYTHONPATH=. python3 examples/worker_job_bus.py
	@PYTHONPATH=. python3 examples/langgraph_backend_sim.py
	@PYTHONPATH=. python3 examples/nats_consumer_once.py
	@PYTHONPATH=. python3 -m aspen_lgw.invoke --transport lab --graph alarm_triage --job-id smoke-inv
	@echo aspen-langgraph-worker smoke ok

nats-e2e:
	@bash scripts/nats_e2e_lab.sh
