PYTHON ?= python3

test:
	$(PYTHON) -m pytest tests/unit/

# Local live-API smoke checks. example/ is gitignored and is not published.
run:
	$(PYTHON) example/test.py

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
