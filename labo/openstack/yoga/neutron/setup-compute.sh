#!/bin/bash -xe

source ../envrc

systemctl status neutron-linuxbridge-agent || systemd-run --unit neutron-linuxbridge-agent -- \
	/opt/neutron/bin/neutron-linuxbridge-agent --log-file /var/log/neutron/neutron-linuxbridge-agent.log \
	--config-file /etc/neutron/neutron.conf \
	--config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
	--config-file /etc/neutron/plugins/ml2/linuxbridge_agent.ini
