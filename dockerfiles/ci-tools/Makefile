mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
IMAGE_NAME := $(current_dir)

.PHONY: all
all:
	sudo docker image build -t "local/${IMAGE_NAME}" .

.PHONY: lint
lint:
	sudo docker run --rm -v .:/ci-tools -w /ci-tools --user "$(id -u):$(id -g)" local/ci-tools ruff check
	sudo docker run --rm -v .:/ci-tools -w /ci-tools --user "$(id -u):$(id -g)" local/ci-tools ansible-lint

.PHONY: format
format:
	echo format
