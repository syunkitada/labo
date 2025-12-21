.PHONY: env
env:
	sudo uv run ansible-playbook labo.infra.labo
	sudo uv run mylabo apply -f manifests/dns

.PHONY: test
test:
	uv run pytest --cov --cov-report=term-missing

.PHONY: bash
bash:
	sudo -E docker run -it --rm --net host -w /workdir -v .:/workdir -u `id -u`:`id -g` local/mytools bash

.PHONY: format
format:
	prettier -w **/*.md
	uv run ruff format

.PHONY: lint
lint:
	prettier -c **/*.md
	uv run ruff check
