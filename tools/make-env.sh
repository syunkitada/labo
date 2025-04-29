#!/bin/bash -xe

cd "$(dirname $0)/../"
LABO_DIR="$PWD"

uv sync

# setup for ansible
sudo mkdir -p /etc/ansible/host_vars
test -L /etc/ansible/ansible.cfg || sudo ln -s "${LABO_DIR}/etc/ansible/ansible.cfg" /etc/ansible/ansible.cfg
test -L /etc/ansible/collections || sudo ln -s "${LABO_DIR}/ansible/collections" /etc/ansible/collections
test -e /etc/ansible/host_vars/localhost.yaml || sudo cp etc/ansible/host_vars/localhost.yaml /etc/ansible/host_vars/
test -L /etc/ansible/roles || sudo ln -s "${LABO_DIR}/ansible/roles" /etc/ansible/

# install tools
for tool in $(find tools -maxdepth 1 -name "labo-*" -printf '%f\n'); do
	test -L "/usr/local/bin/${tool}" || sudo ln -s "$LABO_DIR/tools/$tool" "/usr/local/bin/${tool}"
done
