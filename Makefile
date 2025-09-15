.PHONY: all
all:
	cd labo/tls; make
	sudo .venv/bin/ansible-playbook labo.infra.labo
	sudo .venv/bin/mylabo apply manifests/dns_record.yml

.PHONY: clean
clean:
	rm -rf .venv

.PHONY: test
test:
	uv run pytest

.PHONY: bash
bash:
	sudo -E docker run -it --rm --net host -w /workdir -v .:/workdir -u `id -u`:`id -g` local/mytools bash

.PHONY: format
format:
	prettier -w **/*.md

.PHONY: lint
lint:
	prettier -c **/*.md
