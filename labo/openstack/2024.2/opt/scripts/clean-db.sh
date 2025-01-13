#!/bin/bash -xe

yum install -y mysql

MYSQL_USER=${MYSQL_USER:-"admin"}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-"adminpass"}

mysql -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -h127.0.0.1 -P3306 --protocol=tcp -e "
DROP DATABASE IF EXISTS keystone;
DROP DATABASE IF EXISTS glance;
DROP DATABASE IF EXISTS neutron;
DROP DATABASE IF EXISTS placement;
DROP DATABASE IF EXISTS nova;
DROP DATABASE IF EXISTS nova_api;
DROP DATABASE IF EXISTS nova_cell0;
"
