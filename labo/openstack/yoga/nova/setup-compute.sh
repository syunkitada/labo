#!/bin/bash -xe

source ../envrc

systemctl status nova-compute || systemd-run --unit nova-compute -- \
	/opt/nova/bin/nova-compute --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-compute.log

/opt/nova/bin/nova-manage cell_v2 discover_hosts
