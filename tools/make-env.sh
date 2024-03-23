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

# setup for ssh
sudo mkdir -p /root/.ssh
sudo test -e /root/.ssh/labo.pem || sudo ssh-keygen -t ed25519 -N '' -f /root/.ssh/labo.pem
sudo cp etc/ssh/config /root/.ssh/config
sudo cp /root/.ssh/labo.pem.pub /root/.ssh/authorized_keys

# install tools
for tool in $(find tools -maxdepth 1 -name "labo-*" -printf '%f\n'); do
	test -L "/usr/local/bin/${tool}" || sudo ln -s "$LABO_DIR/tools/$tool" "/usr/local/bin/${tool}"
done

if ! command kind; then
	curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
	sudo install -o root -g root -m 0755 kind /usr/bin/kind
	rm ./kind
fi

if ! commnd helm; then
	curl -Lo helm.tar.gz https://get.helm.sh/helm-v3.14.3-linux-amd64.tar.gz
	tar xf helm.tar.gz
	sudo install -o root -g root -m 0755 linux-amd64/helm /usr/local/bin/helm
	rm -rf linux-amd64
	rm helm.tar.gz
fi

# https://kind.sigs.k8s.io/docs/user/known-issues/#pod-errors-due-to-too-many-open-files
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
