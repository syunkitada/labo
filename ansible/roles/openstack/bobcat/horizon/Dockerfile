FROM local/rocky9-base

COPY . /etc/ansible/roles/horizon

RUN ansible-playbook /etc/ansible/roles/horizon/install.yaml
