upload:
	rm -rf dist/*
	python -m build
	twine upload dist/*
	
clean:
	rm -rf dist/*
	rm -rf build/*
	rm -rf *.egg-info/*