#!/bin/bash -xe

source ../envrc

systemctl status nova-compute || systemd-run --unit nova-compute -- \
	/opt/nova/bin/nova-compute --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-compute.log

source /adminrc
timeout 5 bash -c "until openstack compute service list --service nova-compute | grep $(hostname); do sleep 1; done"
/opt/nova/bin/nova-manage cell_v2 discover_hosts
