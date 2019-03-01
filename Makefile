.PHONY: help test clean build push

.DEFAULT: help

IMAGE_TAG ?= "latest"

help:
	@echo "Make Help"
	@echo "make test - build and spin up docker containers, run tests"
	@echo "make clean - remove docker containers"

test: clean
	docker-compose build pathman
	docker-compose up --exit-code-from=pathman pathman

build: clean
	IMAGE_TAG=$(IMAGE_TAG) docker-compose build pathman

push: clean
	IMAGE_TAG=$(IMAGE_TAG) docker-compose push pathman

clean:
	docker-compose down
	docker-compose rm
