#!/bin/bash -ex

/etc/ansible/scripts/workstation/bootstrap.sh

cd /etc/ansible/inventories/
/etc/ansible/scripts/ansible-playbook -i /etc/ansible/inventories/hosts.yml labo.openstack_bobcat_host.setup
