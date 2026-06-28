.PHONY: env
env:
	cd infra/dns/ && make
	sudo uv run mylabo apply -f manifests/dns
	cd infra/tls && make
	cd infra/l7lb && make

.PHONY: clean
clean:
	cd infra/dns/ && make clean
	cd infra/l7lb/ && make clean

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
