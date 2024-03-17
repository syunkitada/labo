FROM local/rocky9-base

COPY . /etc/ansible/roles/keystone

RUN ansible-playbook /etc/ansible/roles/keystone/dockerfile_playbook.yml
