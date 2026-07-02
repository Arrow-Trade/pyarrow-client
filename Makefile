PYTHON ?= python3

upload:
	rm -rf dist/*
	$(PYTHON) -m build
	$(PYTHON) -m twine upload dist/*
	
clean:
	rm -rf dist/*
	rm -rf build/*
	rm -rf *.egg-info/*