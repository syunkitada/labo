.PHONY: all
all:
	@make env

.PHONY: env
env:
	sudo -E docker compose up -d

.PHONY: deploy
deploy:
	sudo docker exec -it openstack-bobcat-allinone /etc/ansible/scripts/deploy.sh

.PHONY: clean
clean:
	sudo docker compose down
