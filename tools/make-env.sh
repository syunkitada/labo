#!/bin/bash -xe

cd "$(dirname $0)/../"
LABO_DIR="$PWD"

test -e .venv || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# setup for fabric
test -L /usr/local/bin/fab || sudo ln -s "${LABO_DIR}/.venv/bin/fab" /usr/local/bin/fab

# setup for ansible
sudo mkdir -p /etc/ansible/host_vars
test -L /usr/local/bin/ansible-playbook || sudo ln -s "${LABO_DIR}/.venv/bin/ansible-playbook" /usr/local/bin/ansible-playbook
test -L /etc/ansible/ansible.cfg || sudo ln -s "${LABO_DIR}/ansible/ansible.cfg" /etc/ansible/ansible.cfg
test -e /etc/ansible/host_vars/localhost.yaml || sudo cp etc/ansible/host_vars/localhost.yaml /etc/ansible/host_vars/
test -e /etc/ansible/playbook.yaml || sudo cp etc/ansible/playbook.yaml /etc/ansible/
test -L /etc/ansible/roles || sudo ln -s "${LABO_DIR}/ansible/roles" /etc/ansible/

# setup for ssh
sudo mkdir -p /root/.ssh
sudo test -e /root/.ssh/labo.pem || sudo ssh-keygen -t ed25519 -N '' -f /root/.ssh/labo.pem
sudo cp etc/ssh/config /root/.ssh/config

# sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients libguestfs-tools

# install tools
for tool in $(find tools -maxdepth 1 -name "labo-*" -printf '%f\n'); do
	test -L "/usr/local/bin/${tool}" || sudo ln -s "$LABO_DIR/tools/$tool" "/usr/local/bin/${tool}"
done
