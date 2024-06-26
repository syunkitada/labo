#!/bin/bash -ex

/etc/ansible/scripts/workstation/bootstrap.sh

cd /etc/ansible/inventories/
/etc/ansible/scripts/ansible-playbook -i /etc/ansible/inventories/ctl_hosts.yml labo.infra.bootstrap

# ansible-playbook -i ctl_hosts.yml labo.infra.bootstrap
# ansible-playbook -i ctl_hosts.yml labo.infra.consul
# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.infra.bootstrap
# ansible-playbook -i hv_hosts.yml -i hv_az2_hosts.yml labo.infra.bootstrap
# ansible-playbook -i hv_hosts.yml -i hv_az3_hosts.yml labo.infra.bootstrap
# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.infra.consul
# ansible-playbook -i hv_hosts.yml -i hv_az2_hosts.yml labo.infra.consul
# ansible-playbook -i hv_hosts.yml -i hv_az3_hosts.yml labo.infra.consul

# ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl_k8s
# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.openstack_bobcat.hv
# ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl --tags cmd_nova_discover_hosts
# ansible-playbook -i ctl_hosts.yml labo.infra.bootstrap
# ansible-playbook -i ctl_hosts.yml labo.infra.consul

# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.infra.bootstrap
# ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.infra.consul
