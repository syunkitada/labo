env:
	test -e .venv || python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# ----------------------------------------------------------------------------------------------------
# tester
# ----------------------------------------------------------------------------------------------------
UID := $(shell id -u)
GID := $(shell id -g)

.PHONY: tester
tester:
	cd tester; UID=${UID} GID=${GID} sudo -E docker-compose up -d

tester-build:
	cd tester; UID=${UID} GID=${GID} sudo -E docker-compose build

tester-clean:
	cd tester; UID=${UID} GID=${GID} sudo -E docker-compose down
	ssh-keygen -R 10.100.11.11
	ssh-keygen -R 10.100.11.21
	ssh-keygen -R 10.100.11.22
	ssh-keygen -R 10.100.11.23

tester-ssh-centos7:
	ssh 10.100.11.11
tester-ssh-rocky8:
	ssh 10.100.11.21
tester-bash-centos7:
	sudo docker exec -it tester_centos7_1 bash
tester-bash-rocky8:
	sudo docker exec -it tester_rocky8_1 bash
