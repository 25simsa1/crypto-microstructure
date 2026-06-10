PY := .venv/bin/python

.PHONY: all data analyses backtest findings test lint typecheck check clean

all: data analyses backtest findings

data:            ## refresh parquet store + data-quality report
	$(PY) scripts/build_data.py

analyses: data   ## run the four studies (PNG + md each)
	$(PY) scripts/analysis_seasonality.py
	$(PY) scripts/analysis_imbalance.py
	$(PY) scripts/analysis_leadlag.py
	$(PY) scripts/analysis_volclustering.py

backtest: data   ## strategy family vs random null
	$(PY) scripts/run_backtest.py

findings:        ## assemble FINDINGS.md from the latest outputs
	$(PY) scripts/build_findings.py

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check src tests scripts

typecheck:
	.venv/bin/mypy src

check: lint typecheck test

clean:
	rm -rf parquet output .pytest_cache .mypy_cache .ruff_cache
