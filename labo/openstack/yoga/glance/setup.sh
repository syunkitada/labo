#!/bin/bash -xe

source envrc

mysql -e 'CREATE DATABASE IF NOT EXISTS glance'

source /adminrc

service_list=$(openstack service list)
if [[ ! $service_list =~ " glance " ]]; then
	openstack service create --name glance --description "OpenStack Image" image
	openstack endpoint create --region "${OS_REGION}" image public "http://${OS_HOST}:9292"
	openstack endpoint create --region "${OS_REGION}" image internal "http://${OS_HOST}:9292"
	openstack endpoint create --region "${OS_REGION}" image admin "http://${OS_HOST}:9292"
fi

mkdir -p /etc/glance
mkdir -p /var/log/glance
mkdir -p /var/lib/glance/images/

cp glance-api.conf /etc/glance/glance-api.conf
sed -i "s/@MYSQL_USER/${MYSQL_USER}/g" /etc/glance/glance-api.conf
sed -i "s/@MYSQL_PASS/${MYSQL_PASS}/g" /etc/glance/glance-api.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/glance/glance-api.conf

sed -i "s/@OS_REGION/${OS_REGION}/g" /etc/glance/glance-api.conf
sed -i "s/@OS_SERVICE_USER/${OS_SERVICE_USER}/g" /etc/glance/glance-api.conf
sed -i "s/@OS_SERVICE_PASS/${OS_SERVICE_PASS}/g" /etc/glance/glance-api.conf

/opt/glance/bin/glance-manage db_sync

cp /opt/openstack/glance/etc/glance-api-paste.ini /etc/glance/
systemctl status glance-api || systemd-run --unit glance-api -- \
	/opt/glance/bin/glance-api --config-file /etc/glance/glance-api.conf

# test api
timeout 5 bash -c 'until openstack image list; do sleep 1; done'
