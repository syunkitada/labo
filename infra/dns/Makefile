.PHONY: all
all:
	docker compose up -d --build
	./scripts/setup.sh

.PHONY: clean
clean:
	docker compose down
