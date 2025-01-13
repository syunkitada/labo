.PHONY: all
all:
	tools/make-env.sh
	cd labo/tls; make
	sudo ansible-playbook labo.infra.labo

.PHONY: test
test:
	pytest -x -vv fabfile_tests

.PHONY: bash
bash:
	sudo -E docker run -it --rm --net host -w /workdir -v .:/workdir -u `id -u`:`id -g` local/mytools bash

.PHONY: format
format:
	prettier -w **/*.md

.PHONY: lint
lint:
	prettier -c **/*.md
