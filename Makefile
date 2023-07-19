SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -O extglob -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

ifeq ($(.DEFAULT_GOAL),)
ifneq ($(shell test -f .env; echo $$?), 0)
$(error Cannot find a .env file; copy .env.sample and customise)
endif
endif

# Wrap the build in a check for an existing .env file
ifeq ($(shell test -f .env; echo $$?), 0)
include .env
ENVVARS := $(shell sed -ne 's/ *\#.*$$//; /./ s/=.*$$// p' .env )
$(foreach var,$(ENVVARS),$(eval $(shell echo export $(var)="$($(var))")))

.DEFAULT_GOAL := help

VERSION := $(shell cat ./VERSION)
COMMIT_HASH := $(shell git log -1 --pretty=format:"sha-%h")
PLATFORMS := "linux/arm64,linux/amd64"

BUILD_FLAGS ?= 

INDIEAUTHIFY := indieauthify
INDIEAUTHIFY_BUILDER := $(INDIEAUTHIFY)-builder
INDIEAUTHIFY_REPO := ${GITHUB_REGISTRY}/${GITHUB_USER}
INDIEAUTHIFY_IMAGE := ${INDIEAUTHIFY}
INDIEAUTHIFY_DOCKERFILE := ./docker/${INDIEAUTHIFY}/Dockerfile

DOCKER_ENV_FILE := .env.docker

HADOLINT_IMAGE := hadolint/hadolint

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' Makefile

.PHONY: setup
setup:	## Install dependencies
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	(cd theme && yarn install)

static/assets/css/theme.css: theme/src/css/tailwind.css $(wildcard templates/*.html.j2) $(wildcard templates/includes/*.html.j2)
	(cd theme && npx tailwindcss --input src/css/tailwind.css --output ../$@)

.PHONY: theme
theme: static/assets/css/theme.css

.PHONY: typed
typed:		## Check all types with mypy
	mypy indieauthify_server

.PHONY: prettify
prettify:	## Prettify all source code
	yapf --in-place --recursive indieauthify_server

.PHONY: lint
lint: prettify lint-pylint lint-flake8 typed lint-docker	## Run all linters on the code base

.PHONY: lint-pylint
lint-pylint:	## Run pylint on the code base
	pylint --verbose -j 4 --reports yes --recursive yes indieauthify_server

.PHONY: lint-flake8
lint-flake8:	## Run flake8 on the code base
	flake8 -j 4 indieauthify_server

.PHONY: lint-docker
lint-docker: lint-compose lint-dockerfiles ## Lint all Docker related files

.PHONY: lint-compose
lint-compose:	## Lint docker-compose.yml
	docker compose -f docker-compose.yml config 1> /dev/null

.PHONY: lint-dockerfiles
.PHONY: _lint-dockerfiles ## Lint all Dockerfiles
lint-dockerfiles: lint-${INDIEAUTHIFY}-dockerfile

.PHONY: lint-${INDIEAUTHIFY}-dockerfile
lint-${INDIEAUTHIFY}-dockerfile:
	$(MAKE) _lint_dockerfile -e BUILD_DOCKERFILE="${INDIEAUTHIFY_DOCKERFILE}"

BUILD_TARGETS := theme build_indieauthify

.PHONY: build
build: $(BUILD_TARGETS) ## Build all images

REBUILD_TARGETS := rebuild_indieauthify

.PHONY: rebuild
rebuild: $(REBUILD_TARGETS) ## Rebuild all images (no cache)

# indieauthify targets

build_indieauthify:	repo_login ## Build the indieauthify image
	$(MAKE) _build_image \
		-e BUILD_DOCKERFILE=./docker/$(INDIEAUTHIFY)/Dockerfile \
		-e BUILD_IMAGE=$(INDIEAUTHIFY_IMAGE)

rebuild_indieauthify: repo_login	## Rebuild the indieauthify image (no cache)
	$(MAKE) _build_image \
		-e BUILD_DOCKERFILE=./docker/$(INDIEAUTHIFY)/Dockerfile \
		-e BUILD_IMAGE=$(INDIEAUTHIFY_IMAGE) \
		-e BUILD_FLAGS="--no-cache"

.PHONY: up
up: _env_check repo_login	## Bring the indieauthify container stack up
	docker compose --env-file $(DOCKER_ENV_FILE) up -d

.PHONY: down
down: _env_check repo_login	## Bring the indieauthify container stack down
	docker compose --env-file $(DOCKER_ENV_FILE) down

.PHONY: restart
restart: down up	## Restart the indieauthify container stack

.PHONY: destroy
destroy:	## Bring the indieauthify container stack down (removing volumes)
	docker compose --env-file $(DOCKER_ENV_FILE) down -v

.PHONY: _env_check
_env_check:
	@test -s $(DOCKER_ENV_FILE) || { echo "Cannot find $(DOCKER_ENV_FILE); copy .env.docker.sample and customise"; false; }

.PHONY: _lint_dockerfile
_lint_dockerfile:
	docker run --rm -i -e HADOLINT_IGNORE=DL3008 ${HADOLINT_IMAGE} < ${BUILD_DOCKERFILE}

.PHONY: _build_image
_build_image:
	docker buildx inspect $(INDIEAUTHIFY_BUILDER) > /dev/null 2>&1 || \
		docker buildx create --name $(INDIEAUTHIFY_BUILDER) --bootstrap --use
	docker buildx build --platform=$(PLATFORMS) \
		--progress auto \
		--file ${BUILD_DOCKERFILE} --push \
		--tag ${INDIEAUTHIFY_REPO}/${BUILD_IMAGE}:latest \
		--tag ${INDIEAUTHIFY_REPO}/${BUILD_IMAGE}:$(VERSION) \
		--tag ${INDIEAUTHIFY_REPO}/${BUILD_IMAGE}:$(COMMIT_HASH) \
		--build-arg VERSION=${VERSION} \
		--provenance=false \
		--sbom=false \
		$(BUILD_FLAGS) \
		--ssh default $(BUILD_FLAGS) .

.PHONY: repo_login
repo_login:		## Login to the container registry
	echo "${GITHUB_PAT}" | docker login ${GITHUB_REGISTRY} -u ${GITHUB_USER} --password-stdin

# No .env file; fail the build
else
.DEFAULT:
	$(error Cannot find a .env file; copy .env.sample and customise)
endif
