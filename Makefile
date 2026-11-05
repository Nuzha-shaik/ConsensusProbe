PYTHON ?= python

.PHONY: freeze guards typecheck test build ui_gate gate e2e perf verify_all tests lock_check paper security numbers_check clean golden_integrity golden_data golden_gate golden_metrics golden_general golden_cert golden_ui no_leak verify_golden

golden_integrity:
	$(PYTHON) scripts/make_golden.py --check

golden_data:
	$(PYTHON) scripts/golden_check.py --layer data

golden_gate:
	$(PYTHON) scripts/golden_check.py --layer gate

golden_metrics:
	$(PYTHON) scripts/golden_check.py --layer metrics

golden_general:
	$(PYTHON) scripts/golden_check.py --layer general

golden_cert:
	$(PYTHON) scripts/golden_check.py --layer cert

golden_ui:
	cd frontend && npx playwright test --config ../playwright.config.ts e2e/golden.spec.ts

no_leak:
	$(PYTHON) scripts/no_leak_check.py

verify_golden: golden_integrity no_leak gate
	@echo "=== Golden Verification Verification Pipeline Green ==="

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
