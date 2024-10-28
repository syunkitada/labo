all:
	apt install golang-cfssl
	./scripts/make.sh
	sudo docker compose up -d

clean:
	sudo docker compose down
