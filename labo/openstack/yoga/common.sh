#!/bin/bash -xe

source envrc

systemctl start mysql
systemctl start memcached
systemctl start rabbitmq-server

mysql -e "CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASS}'"
mysql -e "GRANT ALL ON *.* TO '${MYSQL_USER}'@'%'; FLUSH PRIVILEGES;"

# osclient
which /usr/local/bin/openstack || ln -s /opt/osclient/bin/openstack /usr/local/bin/openstack

# rabbitmq
rabbitmqctl list_users | grep "${RABBITMQ_USER}" || rabbitmqctl add_user "${RABBITMQ_USER}" "${RABBITMQ_PASS}"
rabbitmqctl set_permissions openstack ".*" ".*" ".*"
