env:
	# for fabfile
	test -e .venv || python3 -m venv .venv
	.venv/bin/pip install -r fabfile/requirements.txt

docker-image-centos7-nwnode:
	sudo docker build -t labo/centos7-nwnode ./docker/images/centos7-nwnode
docker-image-rocky8-nwnode:
	sudo docker build -t labo/centos7-nwnode ./docker/images/rocky8-nwnode
docker-push-centos7-nwnode:
	sudo docker image tag labo/centos7-nwnode localhost:5000/labo/centos7-nwnode:latest
	sudo docker push localhost:5000/labo/centos7-nwnode:latest
