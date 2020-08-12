.PHONY: help test clean clean-min clean-docker clean-test clean-build \
	clean-pyc clean-test clean-docker clean-docs docs servedocs

.DEFAULT: help

IMAGE_TAG ?= "latest"

help:
	@echo "Make Help"
	@echo "make test - build and spin up docker containers, run tests"
	@echo "make clean - shut down docker container, clean up docs"

test: clean
	docker-compose build pathman
	docker-compose up --exit-code-from=pathman pathman

build: clean
	IMAGE_TAG=$(IMAGE_TAG) docker-compose build pathman

push: clean
	IMAGE_TAG=$(IMAGE_TAG) docker-compose push pathman

clean: clean-build clean-pyc clean-test clean-docker clean-docs

clean-min: clean-build clean-pyc clean-test clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-docker:
	docker-compose down
	docker-compose rm

clean-docs:
	rm -rf docs/_build

docs: clean-docs
	cd docs/ && $(MAKE) html

servedocs: docs
	cd docs/_build/html && python -m http.server
