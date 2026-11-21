# CPPI_2021 - environment and run targets
PYTHON      ?= python3
VENV        := .venv
BIN         := $(VENV)/bin
NOTEBOOK    := CPPI_2021.ipynb
KERNEL_NAME := cppi

.DEFAULT_GOAL := help
.PHONY: help setup venv install kernel bloomberg lab run check freeze clean distclean

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

lab: setup  ## Open the notebook in JupyterLab
	$(BIN)/jupyter lab $(NOTEBOOK)

run: setup  ## Execute the notebook top to bottom and save outputs in place
	MPLBACKEND=Agg $(BIN)/jupyter nbconvert --to notebook --execute --inplace $(NOTEBOOK)

check: setup  ## Execute the notebook without modifying it (smoke test)
	MPLBACKEND=Agg $(BIN)/jupyter nbconvert --to notebook --execute $(NOTEBOOK) --output-dir build --output cppi_check

freeze:  ## Print the full list of installed package versions
	$(BIN)/pip freeze

clean:  ## Remove caches and notebook checkpoints
	rm -rf __pycache__ .ipynb_checkpoints build

distclean: clean  ## Also remove the virtual environment and the Jupyter kernel
	-$(BIN)/jupyter kernelspec remove -f $(KERNEL_NAME)
	rm -rf $(VENV)
