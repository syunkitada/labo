.PHONY: all
all:
	tools/make-env.sh
	cd labo/tls; make
	sudo ansible-playbook labo.infra.labo

.PHONY: test
test:
	pytest -x -vv fabfile_tests
