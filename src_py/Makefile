.ONESHELL:

.PHONY: install

VENV_DIR := .venv

install: $(VENV_DIR)

$(VENV_DIR):
	rm -rf $(VENV_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate
	python3 -m pip install -r requirements.txt
