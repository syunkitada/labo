#!/bin/bash -xe

source ../envrc

mysql -e 'CREATE DATABASE IF NOT EXISTS nova_api'
mysql -e 'CREATE DATABASE IF NOT EXISTS nova'
mysql -e 'CREATE DATABASE IF NOT EXISTS nova_cell0'

source /adminrc

service_list=$(openstack service list)
if [[ ! $service_list =~ " compute " ]]; then
	openstack service create --name nova --description "OpenStack Compute" compute
	openstack endpoint create --region "${OS_REGION}" compute public "http://${OS_HOST}:8774/v2.1"
	openstack endpoint create --region "${OS_REGION}" compute internal "http://${OS_HOST}:8774/v2.1"
	openstack endpoint create --region "${OS_REGION}" compute admin "http://${OS_HOST}:8774/v2.1"
fi

mkdir -p /etc/nova
mkdir -p /var/log/nova

cp /opt/openstack/nova/etc/nova/api-paste.ini /etc/nova/

cp nova.conf /etc/nova/nova.conf
sed -i "s/@MYSQL_USER/${MYSQL_USER}/g" /etc/nova/nova.conf
sed -i "s/@MYSQL_PASS/${MYSQL_PASS}/g" /etc/nova/nova.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/nova/nova.conf

sed -i "s/@OS_REGION/${OS_REGION}/g" /etc/nova/nova.conf
sed -i "s/@OS_SERVICE_USER/${OS_SERVICE_USER}/g" /etc/nova/nova.conf
sed -i "s/@OS_SERVICE_PASS/${OS_SERVICE_PASS}/g" /etc/nova/nova.conf

sed -i "s/@RABBITMQ_USER/${RABBITMQ_USER}/g" /etc/nova/nova.conf
sed -i "s/@RABBITMQ_PASS/${RABBITMQ_PASS}/g" /etc/nova/nova.conf

MY_IP=$(ip addr show eth0 | grep inet | awk '{print $2}' | awk -F '/' '{print $1}')
sed -i "s/@MY_IP/${MY_IP}/g" /etc/nova/nova.conf

/opt/nova/bin/nova-manage api_db sync
/opt/nova/bin/nova-manage cell_v2 map_cell0
/opt/nova/bin/nova-manage cell_v2 list_cells | grep ' cell1 ' || /opt/nova/bin/nova-manage cell_v2 create_cell --name=cell1 --verbose
/opt/nova/bin/nova-manage db sync

systemctl status nova-api || systemd-run --unit nova-api -- \
	/opt/nova/bin/nova-api --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-api.log
systemctl status nova-scheduler || systemd-run --unit nova-scheduler -- \
	/opt/nova/bin/nova-scheduler --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-scheduler.log
systemctl status nova-conductor || systemd-run --unit nova-conductor -- \
	/opt/nova/bin/nova-conductor --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-conductor.log
systemctl status nova-novncproxy || systemd-run --unit nova-novncproxy -- \
	/opt/nova/bin/nova-novncproxy --config-file /etc/nova/nova.conf --log-file /var/log/nova/nova-novncproxy.log
