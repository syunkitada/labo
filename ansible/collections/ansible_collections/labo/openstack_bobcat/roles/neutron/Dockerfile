FROM local/rocky9-base

COPY . /etc/ansible/roles/neutron

RUN ansible-playbook /etc/ansible/roles/neutron/dockerfile_playbook.yml
