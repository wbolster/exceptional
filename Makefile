.PHONY: all doc test dist upload

all: test

doc:
	python setup.py build_sphinx

test:
	pytest

dist:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*
