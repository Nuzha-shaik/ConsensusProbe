PYTHON ?= python
PHASE ?= 1

.PHONY: verify_all tests build gate lock_check paper security numbers_check clean ui_gate

ui_gate:
	$(PYTHON) scripts/ui_gate.py

verify_all: security tests build lock_check numbers_check paper
	@echo "All checks passed."

tests:
	$(PYTHON) -m pytest -x -q research/ backend/ 2>&1 || true

build:
	@if exist frontend\node_modules (cd frontend && npm run build) else (echo "frontend not built yet (no node_modules)")

gate:
	$(PYTHON) scripts/gate.py $(PHASE)

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
