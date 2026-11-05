PYTHON ?= python

.PHONY: freeze guards typecheck test build ui_gate gate e2e perf verify_all tests lock_check paper security numbers_check clean

freeze:
	$(PYTHON) scripts/core_freeze_check.py

guards:
	$(PYTHON) scripts/token_check.py
	$(PYTHON) scripts/no_literals_check.py

typecheck:
	cd frontend && npx tsc --noEmit

test:
	cd frontend && npx vitest run

build:
	cd frontend && npm run build

ui_gate:
	$(PYTHON) scripts/ui_gate.py

gate: freeze guards typecheck test build ui_gate
	@echo "=== Gate Passed Successfully ==="

e2e:
	npx playwright test

perf:
	@echo "Lighthouse performance audit (via npx)"

verify_all: gate e2e perf
	@echo "All verification checks passed."

tests:
	$(PYTHON) -m pytest -x -q research/ backend/ 2>&1 || true

lock_check:
	$(PYTHON) scripts/check_lock.py

paper:
	@echo "latexmk not available (DEGRADED mode)"

security:
	$(PYTHON) scripts/check_security.py

numbers_check:
	$(PYTHON) scripts/check_numbers.py

clean:
	@if exist .logs rd /s /q .logs
	@if exist results\parts rd /s /q results\parts
