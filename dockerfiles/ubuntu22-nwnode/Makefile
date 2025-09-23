mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
IMAGE_NAME := $(current_dir)

.PHONY: all
all:
	sudo docker image build -t "local/${IMAGE_NAME}" .

.PHONY: bash
bash:
	sudo docker run -it --rm --net host -w /workdir -v .:/workdir "local/${IMAGE_NAME}" bash
