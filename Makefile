# CPPI 2021 (COLCAP) / CPPI 2026 (gold) - environment and run targets
PYTHON      ?= python3
VENV        := .venv
BIN         := $(VENV)/bin
NOTEBOOKS   := CPPI_2021.ipynb CPPI_2026.ipynb
NB          ?= $(NOTEBOOKS)     # override: make run NB=CPPI_2026.ipynb
KERNEL_NAME := cppi

.DEFAULT_GOAL := help
.PHONY: help setup venv install kernel bloomberg lab run check gold-data freeze clean distclean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: install kernel  ## Create venv, install packages and register the Jupyter kernel

venv: $(BIN)/activate  ## Create the virtual environment

$(BIN)/activate:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: venv  ## Install pinned dependencies
	$(BIN)/pip install -r requirements.txt

kernel: install  ## Register the venv as a Jupyter kernel ("Python 3 (CPPI .venv)")
	$(BIN)/python -m ipykernel install --user --name $(KERNEL_NAME) --display-name "Python 3 (CPPI .venv)"

bloomberg: install  ## Optional: install blpapi for live Bloomberg data
	$(BIN)/pip install -r requirements-bloomberg.txt

lab: setup  ## Open JupyterLab in the project folder
	$(BIN)/jupyter lab

run: setup  ## Execute the notebooks (NB=...) and save outputs in place
	MPLBACKEND=Agg $(BIN)/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 $(NB)

check: setup  ## Execute the notebooks (NB=...) without modifying them; output in build/
	MPLBACKEND=Agg $(BIN)/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 $(NB) --output-dir build

gold-data: install  ## Refresh data/precios_oro.csv from Yahoo Finance
	$(BIN)/python -c "import yfinance as yf; yf.download(['GC=F','GLD','^IRX'], start='2005-01-01', progress=False, auto_adjust=True, threads=False, timeout=30)['Close'].to_csv('data/precios_oro.csv'); print('data/precios_oro.csv actualizado')"

freeze:  ## Print the full list of installed package versions
	$(BIN)/pip freeze

clean:  ## Remove caches and notebook checkpoints
	rm -rf __pycache__ .ipynb_checkpoints build

distclean: clean  ## Also remove the virtual environment and the Jupyter kernel
	-$(BIN)/jupyter kernelspec remove -f $(KERNEL_NAME)
	rm -rf $(VENV)
