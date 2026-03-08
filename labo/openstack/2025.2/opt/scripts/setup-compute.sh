#!/bin/bash -xe

# ----------------------------------------------------------------------------------------------------
# neuton-openvswitch-agent
# ----------------------------------------------------------------------------------------------------

dnf install -y \
	https://mirror.stream.centos.org/SIGs/9-stream/nfv/x86_64/openvswitch-2/Packages/o/openvswitch3.1-3.1.0-65.el9s.x86_64.rpm \
	https://mirror.stream.centos.org/SIGs/9-stream/nfv/x86_64/openvswitch-2/Packages/o/openvswitch-selinux-extra-policy-1.0-31.el9s.noarch.rpm

cp /opt/openstack/neutron/openvswitch_agent.ini /etc/neutron/plugins/ml2/openvswitch_agent.ini
cp /opt/openstack/neutron/metadata_agent.ini /etc/neutron/plugins/ml2/metadata_agent.ini
cp /opt/openstack/neutron/dhcp_agent.ini /etc/neutron/plugins/ml2/dhcp_agent.ini

systemctl start openvswitch

systemctl reset-failed neutron-openvswitch-agent || echo 'ignored'
systemctl status neutron-openvswitch-agent ||
	systemd-run --unit neutron-openvswitch-agent -- \
		/opt/neutron/bin/neutron-openvswitch-agent \
		--config-file /etc/neutron/neutron.conf \
		--config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
		--config-file /etc/neutron/plugins/ml2/openvswitch_agent.ini
systemctl restart neutron-openvswitch-agent


# ----------------------------------------------------------------------------------------------------
# nova-compute
# ----------------------------------------------------------------------------------------------------

dnf config-manager --set-enabled crb
dnf clean all
dnf install -y genisoimage qemu-kvm libvirt libvirt-devel gcc

/opt/nova/bin/pip install libvirt-python

cp /opt/openstack/nova/nova-compute.conf /etc/nova/nova-compute.conf

test -L /usr/bin/nova-rootwrap || ln -s /opt/nova/bin/nova-rootwrap /usr/bin/

systemctl start libvirtd

systemctl reset-failed nova-compute || echo 'ignored'
systemctl status nova-compute ||
	systemd-run --unit nova-compute -- \
		/opt/nova/bin/nova-compute \
		--config-file /etc/nova/nova.conf \
		--config-file /etc/nova/nova-compute.conf
systemctl restart nova-compute

sleep 20

/opt/nova/bin/nova-manage cell_v2 discover_hosts
