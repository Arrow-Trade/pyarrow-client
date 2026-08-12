PYTHON ?= python3

test:
	$(PYTHON) example/test.py

# Closing Auction Session full-mode check (equities + nearest ATM CE/PE).
# Runs continuously until Ctrl+C. Optional: CAS_SYMBOLS=... CAS_DURATION=120
cas:
	$(PYTHON) example/cas.py

upload:
	rm -rf dist/*
	$(PYTHON) -m build
	$(PYTHON) -m twine upload dist/*
	
clean:
	rm -rf dist/*
	rm -rf build/*
	rm -rf *.egg-info/*