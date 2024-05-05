#!/bin/bash -ex

cd /etc/ansible/inventories/
ansible-playbook -i ctl_hosts.yml labo.infra.bootstrap

# ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl_k8s
# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.openstack_bobcat.hv
# ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl --tags cmd_nova_discover_hosts
