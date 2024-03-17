FROM local/bobcat-nova:latest

COPY . /etc/ansible/roles/nova_compute

RUN ansible-playbook /etc/ansible/roles/nova_compute/dockerfile_playbook.yml

ENV PATH=/opt/nova/bin:/root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
