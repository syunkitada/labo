env:
	# for fabfile
	test -e .venv || python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	sudo mkdir -p /var/run/netns
	sudo mkdir -p /root/.ssh
	sudo mkdir -p /etc/ansible
	test -e /etc/ansible/vars.yaml || sudo cp etc/ansible/vars.yaml /etc/ansible/
	sudo test -e /root/.ssh/labo.pem || sudo ssh-keygen -t ed25519 -N '' -f /root/.ssh/labo.pem
	sudo cp etc/ssh/config /root/.ssh/config

infra:
	bash -c "source binrc && labo-ansible-playbook nfs"
	bash -c "source binrc && labo-ansible-playbook docker"
	bash -c "source binrc && labo-ansible-playbook docker-registry-docker"
	bash -c "source binrc && labo-ansible-playbook mysql-docker"
	bash -c "source binrc && labo-ansible-playbook pdns-docker"

# TODO
# docker-registry:
# 	./labo/docker/docker.sh setup-registry
# docker-push-centos7-nwnode:
# 	sudo docker image tag labo/centos7-nwnode localhost:5000/labo/centos7-nwnode:latest
# 	sudo docker push localhost:5000/labo/centos7-nwnode:latest
# docker-push-rocky8-nwnode:
# 	sudo docker image tag labo/rocky8-nwnode localhost:5000/labo/rocky8-nwnode:latest
# 	sudo docker push localhost:5000/labo/rocky8-nwnode:latest
# docker-push-ubuntu20-nwnode:
# 	sudo docker image tag labo/ubuntu20-nwnode localhost:5000/labo/ubuntu20-nwnode:latest
# 	sudo docker push localhost:5000/labo/ubuntu20-nwnode:latest
# docker-push-ubuntu22-nwnode:
# 	sudo docker image tag labo/ubuntu22-nwnode localhost:5000/labo/ubuntu22-nwnode:latest
# 	sudo docker push localhost:5000/labo/ubuntu22-nwnode:latest

test:
	pytest -x -vv fabfile_tests
