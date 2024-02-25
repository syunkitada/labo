env:
	tools/make-env.sh
	sudo ansible-playbook /etc/ansible/playbook.yaml

test:
	pytest -x -vv fabfile_tests
