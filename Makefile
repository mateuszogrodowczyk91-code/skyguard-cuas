.PHONY: help install test demo lint semgrep docker-build docker-demo clean

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

help:
	@echo "SKYGUARD portfolio targets:"
	@echo "  make install   - create venv + install deps"
	@echo "  make test      - unit + extras + e2e demo"
	@echo "  make demo      - emulation demo only"
	@echo "  make lint      - ruff check"
	@echo "  make docker-demo - build & run demo in Docker (if docker available)"

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -U pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install pytest ruff

test:
	PYTHON=$(BIN)/python ./scripts/run_tests.sh

demo:
	PYTHON=$(BIN)/python ./scripts/run_demo.sh

lint:
	$(BIN)/ruff check furnace/lib furnace/07_Emulation furnace/08_Evidence_API furnace/06_Testy_Automatyczne

docker-build:
	docker build -t skyguard-portfolio:local .

docker-demo: docker-build
	docker compose run --rm skyguard-demo

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	rm -f furnace/08_Evidence_API/evidence_chain.json furnace/logs/*.log furnace_blackbox_fallback.log 2>/dev/null || true
