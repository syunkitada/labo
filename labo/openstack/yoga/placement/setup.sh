#!/bin/bash -xe

source envrc

mysql -e 'CREATE DATABASE IF NOT EXISTS placement'

source /adminrc

service_list=$(openstack service list)
if [[ ! $service_list =~ " placement " ]]; then
	openstack service create --name placement --description "OpenStack Placement" placement
	openstack endpoint create --region "${OS_REGION}" placement public "http://${OS_HOST}:8778"
	openstack endpoint create --region "${OS_REGION}" placement internal "http://${OS_HOST}:8778"
	openstack endpoint create --region "${OS_REGION}" placement admin "http://${OS_HOST}:8778"
fi

mkdir -p /etc/placement
mkdir -p /var/log/placement

cp placement.conf /etc/placement/placement.conf
sed -i "s/@MYSQL_USER/${MYSQL_USER}/g" /etc/placement/placement.conf
sed -i "s/@MYSQL_PASS/${MYSQL_PASS}/g" /etc/placement/placement.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/placement/placement.conf

sed -i "s/@OS_REGION/${OS_REGION}/g" /etc/placement/placement.conf
sed -i "s/@OS_SERVICE_USER/${OS_SERVICE_USER}/g" /etc/placement/placement.conf
sed -i "s/@OS_SERVICE_PASS/${OS_SERVICE_PASS}/g" /etc/placement/placement.conf

/opt/placement/bin/placement-manage db sync

systemctl status placement-api || systemd-run --unit placement-api -- \
	/opt/placement/bin/placement-api --port 8778

curl http://localhost:8778/

# test api
timeout 5 bash -c 'until openstack resource class list; do sleep 1; done'
