.PHONY: help test clean clean-docker clean-test docs servedocs

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

clean: clean-docker clean-docs

clean-docker:
	docker-compose down
	docker-compose rm

clean-docs:
	rm -rf docs/_build

docs: clean-docs
	cd docs/ && $(MAKE) html

servedocs: docs
	cd docs/_build/html && python -m http.server
