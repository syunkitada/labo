FROM local/rocky9-base

COPY . /etc/ansible/roles/placement

RUN ansible-playbook /etc/ansible/roles/placement/dockerfile_playbook.yml
