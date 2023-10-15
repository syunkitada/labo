env:
	# for fabfile
	test -e .venv || python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@docker
	@docker-registry

docker:
	./labo/docker/docker.sh setup
docker-registry:
	./labo/docker/docker.sh setup-registry
docker-image-centos7-nwnode:
	sudo docker build -t labo/centos7-nwnode ./labo/docker/images/centos7-nwnode
docker-image-rocky8-base:
	sudo docker build -t labo/rocky8-base ./labo/docker/images/rocky8-base
docker-image-rocky8-nwnode:
	sudo docker build -t labo/rocky8-nwnode ./labo/docker/images/rocky8-nwnode
docker-image-ubuntu20-nwnode:
	sudo docker build -t labo/ubuntu20-nwnode ./labo/docker/images/ubuntu20-nwnode
docker-image-ubuntu22-base:
	sudo docker build -t labo/ubuntu22-base ./labo/docker/images/ubuntu22-base
docker-image-ubuntu22-nwnode:
	sudo docker build -t labo/ubuntu22-nwnode ./labo/docker/images/ubuntu22-nwnode
docker-push-centos7-nwnode:
	sudo docker image tag labo/centos7-nwnode localhost:5000/labo/centos7-nwnode:latest
	sudo docker push localhost:5000/labo/centos7-nwnode:latest
docker-push-rocky8-nwnode:
	sudo docker image tag labo/rocky8-nwnode localhost:5000/labo/rocky8-nwnode:latest
	sudo docker push localhost:5000/labo/rocky8-nwnode:latest
docker-push-ubuntu20-nwnode:
	sudo docker image tag labo/ubuntu20-nwnode localhost:5000/labo/ubuntu20-nwnode:latest
	sudo docker push localhost:5000/labo/ubuntu20-nwnode:latest
docker-push-ubuntu22-nwnode:
	sudo docker image tag labo/ubuntu22-nwnode localhost:5000/labo/ubuntu22-nwnode:latest
	sudo docker push localhost:5000/labo/ubuntu22-nwnode:latest

test:
	pytest -x -vv fabfile_tests
