#!/bin/bash -xe

cd "$(dirname $0)/../"
LABO_DIR="$PWD"

test -e .venv || python3 -m venv .venv --system
.venv/bin/pip install -r requirements.txt

# setup for fabric
test -L /usr/local/bin/fab || sudo ln -s "${LABO_DIR}/.venv/bin/fab" /usr/local/bin/fab

# setup for ansible
sudo mkdir -p /etc/ansible/host_vars
test -L /usr/local/bin/ansible-playbook || sudo ln -s "${LABO_DIR}/.venv/bin/ansible-playbook" /usr/local/bin/ansible-playbook
test -L /usr/local/bin/ansible-galaxy || sudo ln -s "${LABO_DIR}/.venv/bin/ansible-galaxy" /usr/local/bin/ansible-galaxy
test -L /usr/local/bin/ansible-lint || sudo ln -s "${LABO_DIR}/.venv/bin/ansible-lint" /usr/local/bin/ansible-lint
test -L /etc/ansible/ansible.cfg || sudo ln -s "${LABO_DIR}/etc/ansible/ansible.cfg" /etc/ansible/ansible.cfg
test -L /etc/ansible/collections || sudo ln -s "${LABO_DIR}/ansible/collections" /etc/ansible/collections
test -e /etc/ansible/host_vars/localhost.yaml || sudo cp etc/ansible/host_vars/localhost.yaml /etc/ansible/host_vars/
test -L /etc/ansible/roles || sudo ln -s "${LABO_DIR}/ansible/roles" /etc/ansible/

# install tools
for tool in $(find tools -maxdepth 1 -name "labo-*" -printf '%f\n'); do
	test -L "/usr/local/bin/${tool}" || sudo ln -s "$LABO_DIR/tools/$tool" "/usr/local/bin/${tool}"
done
