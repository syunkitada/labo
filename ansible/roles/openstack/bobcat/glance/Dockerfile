FROM local/rocky9-base

COPY . /etc/ansible/roles/glance

RUN ansible-playbook /etc/ansible/roles/glance/install.yaml
