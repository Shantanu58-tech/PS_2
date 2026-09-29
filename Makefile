.PHONY: setup demo live test eval verify scenario lint

setup:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

demo:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev

live:
	MODE=live cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	cd backend && python -m pytest tests/ -v

eval:
	cd backend && python -m eval.run_all

verify:
	cd backend && python -m ledger.verify --db data/satya.db

scenario:
	cd backend && python -m scenario.generate --seed 7 --output replay/scenario_v1.jsonl

lint:
	cd backend && ruff check app/ && mypy app/
