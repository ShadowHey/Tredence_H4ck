.PHONY: all install seed backend frontend test-backend test-frontend test-e2e test lint build clean

all: test

install:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install --upgrade pip
	backend/.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install --legacy-peer-deps
	cd e2e && npm install

seed:
	backend/.venv/bin/python scripts/seed_catalogue.py

backend:
	cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- -p 3000

test-backend:
	backend/.venv/bin/pytest backend/tests

test-frontend:
	cd frontend && npm test

test-e2e:
	cd e2e && npx playwright test

test: test-backend test-frontend

lint:
	cd frontend && npm run lint && npx tsc --noEmit

build:
	cd frontend && npm run build

clean:
	rm -rf backend/.pytest_cache backend/__pycache__ frontend/.next
