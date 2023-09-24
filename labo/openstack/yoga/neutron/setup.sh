#!/bin/bash -xe

source ../envrc

mysql -e 'CREATE DATABASE IF NOT EXISTS neutron'

source /adminrc

service_list=$(openstack service list)
if [[ ! $service_list =~ " network " ]]; then
	openstack service create --name nova --description "OpenStack Networking" network
	openstack endpoint create --region "${OS_REGION}" network public "http://${OS_HOST}:9696"
	openstack endpoint create --region "${OS_REGION}" network internal "http://${OS_HOST}:9696"
	openstack endpoint create --region "${OS_REGION}" network admin "http://${OS_HOST}:9696"
fi

mkdir -p /etc/neutron
mkdir -p /etc/neutron/plugins/ml2
mkdir -p /var/log/neutron
mkdir -p /var/lib/neutron

cp /opt/openstack/neutron/etc/api-paste.ini /etc/neutron/
cp /opt/openstack/neutron/etc/rootwrap.conf /etc/neutron/

cp ml2_conf.ini /etc/neutron/plugins/ml2/ml2_conf.ini
cp linuxbridge_agent.ini /etc/neutron/plugins/ml2/linuxbridge_agent.ini
cp neutron.conf /etc/neutron/neutron.conf
cp dhcp_agent.ini /etc/neutron/dhcp_agent.ini
cp metadata_agent.ini /etc/neutron/metadata_agent.ini
sed -i "s/@MYSQL_USER/${MYSQL_USER}/g" /etc/neutron/neutron.conf
sed -i "s/@MYSQL_PASS/${MYSQL_PASS}/g" /etc/neutron/neutron.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/neutron/neutron.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/neutron/metadata_agent.ini

sed -i "s/@OS_REGION/${OS_REGION}/g" /etc/neutron/neutron.conf
sed -i "s/@OS_SERVICE_USER/${OS_SERVICE_USER}/g" /etc/neutron/neutron.conf
sed -i "s/@OS_SERVICE_PASS/${OS_SERVICE_PASS}/g" /etc/neutron/neutron.conf

sed -i "s/@RABBITMQ_USER/${RABBITMQ_USER}/g" /etc/neutron/neutron.conf
sed -i "s/@RABBITMQ_PASS/${RABBITMQ_PASS}/g" /etc/neutron/neutron.conf

/opt/neutron/bin/neutron-db-manage --config-file /etc/neutron/neutron.conf \
	--config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head

export PATH=/opt/neutron/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
systemctl status --no-pager neutron-server || systemd-run --unit neutron-server -- \
	/opt/neutron/bin/neutron-server --log-file /var/log/neutron/neutron-server.log \
	--config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini

# systemctl status nova-scheduler || systemd-run --unit nova-scheduler -- \
# 	/opt/nova/bin/nova-scheduler --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-scheduler.log
# systemctl status nova-conductor || systemd-run --unit nova-conductor -- \
# 	/opt/nova/bin/nova-conductor --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-conductor.log
# systemctl status nova-novncproxy || systemd-run --unit nova-novncproxy -- \
# 	/opt/nova/bin/nova-novncproxy --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-novncproxy.log
