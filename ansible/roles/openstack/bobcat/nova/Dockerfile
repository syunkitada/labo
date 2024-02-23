FROM local/rocky9-base

COPY . /etc/ansible/roles/nova

RUN ansible-playbook /etc/ansible/roles/nova/install.yaml
