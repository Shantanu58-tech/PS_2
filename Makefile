.PHONY: setup models demo live test eval eval-quick verify scenario lint build serve check-collectors

PY ?= python

setup:
	cd backend && $(PY) -m pip install -e ".[dev]"
	cd frontend && npm install

models:            ## download the pre-trained models into ./models (HF_TOKEN optional)
	$(PY) scripts/fetch_models.py

scenario:          ## seeded synthetic scenario -> replay/ (+ data/media images)
	cd backend && $(PY) -m scenario.generate --seed 7

demo: build        ## single URL: API + built console on http://localhost:8000
	cd backend && $(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

live:
	cd backend && MODE=live $(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	cd backend && $(PY) -m pytest tests/ -v

eval:              ## writes eval/reports/*.md + eval/reports/summary.json
	cd backend && $(PY) -m eval.run_all

eval-quick:
	cd backend && $(PY) -m eval.run_all --quick

verify:
	cd backend && $(PY) -m app.ledger.verify --db ../data/deepastambha.db

lint:
	cd backend && ruff check app/ eval/ scenario/ && mypy app/
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build

check-collectors:  ## one live pull per collector whose credentials are set
	cd backend && $(PY) ../scripts/check_collectors.py
