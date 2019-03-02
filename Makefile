.PHONY: doc test

doc:
	python setup.py build_sphinx

test:
	pytest
