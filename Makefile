env:
	tools/make-env.sh
	sudo ansible-playbook labo.infra.localhost

test:
	pytest -x -vv fabfile_tests
