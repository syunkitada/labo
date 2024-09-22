.PHONY: all
all:
	./scripts/make-env.sh

# .PHONY: deploy
# deploy:
# 	sudo docker exec -it openstack-bobcat-ansible /etc/ansible/scripts/deploy.sh

.PHONY: clean
clean:
	sudo docker compose down
	kind delete cluster -n kind
