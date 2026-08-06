.PHONY: smoke test
export PYTHONPATH := .
test:
	@python3 -m unittest tests.test_alarm_triage -v
smoke: test
	@PYTHONPATH=. python3 examples/alarm_triage_sim.py
	@PYTHONPATH=. python3 -m aspen_lgw.cli
	@echo aspen-langgraph-worker smoke ok
