#!/bin/bash -xe

yum install -y mysql mysql-server

systemctl start mysqld

MYSQL_USER=${MYSQL_USER:-"admin"}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-"adminpass"}

mysql -e "
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'adminpass';

GRANT ALL ON *.* TO 'admin'@'%';

FLUSH PRIVILEGES;
"

mysql -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -h127.0.0.1 -P3306 --protocol=tcp -e "
CREATE DATABASE IF NOT EXISTS keystone;
CREATE DATABASE IF NOT EXISTS glance;
CREATE DATABASE IF NOT EXISTS neutron;
CREATE DATABASE IF NOT EXISTS placement;
CREATE DATABASE IF NOT EXISTS nova;
CREATE DATABASE IF NOT EXISTS nova_api;
CREATE DATABASE IF NOT EXISTS nova_cell0;
"

# echo "
# [client]
# host=127.0.0.1
# port=3306
# protocol=tcp
# user=admin
# password=adminpass
# " >~/.my.cnf
