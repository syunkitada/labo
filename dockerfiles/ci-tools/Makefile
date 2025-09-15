name = ci-tools

.PHONY: image
image:
	sudo docker image build -t local/$(name) .

.PHONY: lint
lint:
	sudo docker run --rm -v .:/ci-tools -w /ci-tools --user "$(id -u):$(id -g)" local/ci-tools ruff check
	sudo docker run --rm -v .:/ci-tools -w /ci-tools --user "$(id -u):$(id -g)" local/ci-tools ansible-lint

.PHONY: format
format:
	echo format
