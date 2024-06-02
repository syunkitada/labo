env:
	tools/make-env.sh
	sudo ansible-playbook labo.infra.labo

test:
	pytest -x -vv fabfile_tests
