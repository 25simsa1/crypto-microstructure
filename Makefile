PY := .venv/bin/python

.PHONY: all data analyses backtest findings test lint typecheck check clean

all: data analyses backtest replication findings

data:            ## refresh parquet stores + quality reports (both captures)
	$(PY) scripts/build_data.py
	$(PY) scripts/build_venue_data.py

analyses: data   ## run all studies (PNG + md each)
	$(PY) scripts/analysis_seasonality.py
	$(PY) scripts/analysis_imbalance.py
	$(PY) scripts/analysis_leadlag.py
	$(PY) scripts/analysis_volclustering.py
	$(PY) scripts/analysis_epps.py
	$(PY) scripts/analysis_tape.py
	$(PY) scripts/analysis_anomalies.py
	$(PY) scripts/analysis_crossvenue.py

backtest: data   ## strategy family vs random null
	$(PY) scripts/run_backtest.py

replication:     ## run the pre-registered replication (frozen procedure)
	$(PY) scripts/replication_run.py

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
