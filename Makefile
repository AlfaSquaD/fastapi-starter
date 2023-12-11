# Variables
VENV           = .venv
VENV_PYTHON    = $(VENV)/bin/python
SYSTEM_PYTHON  = $(or $(shell which python3), $(shell which python))
PYTHON         = $(or $(wildcard $(VENV_PYTHON)), $(SYSTEM_PYTHON))

create-venv:
	$(PYTHON) -m venv $(VENV)

install: create-venv
	$(VENV_PYTHON) -m pip install -r requirements.txt

run:
	$(VENV_PYTHON) main.py

clean:
	rm -rf $(VENV)

.PHONY: create-venv install run clean