.PHONY: all doc test lint dist upload

all: test lint

doc:
	python setup.py build_sphinx

test:
	pytest

lint:
	flake8 src/exceptional
	black --check --quiet src/* test_*

dist:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*
