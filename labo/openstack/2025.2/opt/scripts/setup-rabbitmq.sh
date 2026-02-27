#!/bin/bash -xe

yum install -y https://github.com/rabbitmq/erlang-rpm/releases/download/v26.2.3/erlang-26.2.3-1.el9.x86_64.rpm
yum install -y https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.12.12/rabbitmq-server-3.12.12-1.el8.noarch.rpm

systemctl start rabbitmq-server

rabbitmqctl add_user admin adminpass || echo "ignore because the user may already exists"

rabbitmqctl add_vhost /nova
rabbitmqctl add_vhost /neutron
rabbitmqctl add_vhost /cinder

rabbitmqctl set_permissions -p /nova admin ".*" ".*" ".*"
rabbitmqctl set_permissions -p /neutron admin ".*" ".*" ".*"
rabbitmqctl set_permissions -p /cinder admin ".*" ".*" ".*"
