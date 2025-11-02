.PHONY: all
all:
	@make env

.PHONY: env
env:
	sudo -E docker compose up -d
	./scripts/kind.sh

.PHONY: deploy
deploy:
	sudo docker exec -it openstack-bobcat-ansible /etc/ansible/scripts/deploy.sh

.PHONY: clean
clean:
	sudo docker compose down
	kind delete cluster -n kind
