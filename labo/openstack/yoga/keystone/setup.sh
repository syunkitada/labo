#!/bin/bash -xe

source envrc

mysql -e 'CREATE DATABASE IF NOT EXISTS keystone'

mkdir -p /etc/keystone
mkdir -p /var/log/keystone

cp keystone.conf /etc/keystone/keystone.conf
sed -i "s/@MYSQL_USER/${MYSQL_USER}/g" /etc/keystone/keystone.conf
sed -i "s/@MYSQL_PASS/${MYSQL_PASS}/g" /etc/keystone/keystone.conf
sed -i "s/@OS_HOST/${OS_HOST}/g" /etc/keystone/keystone.conf

/opt/keystone/bin/keystone-manage db_sync

/opt/keystone/bin/keystone-manage fernet_setup --keystone-user root --keystone-group root
/opt/keystone/bin/keystone-manage credential_setup --keystone-user root --keystone-group root

/opt/keystone/bin/keystone-manage bootstrap --bootstrap-password "${OS_ADMIN_PASS}" \
	--bootstrap-admin-url "http://${OS_HOST}:5000/v3/" \
	--bootstrap-internal-url "http://${OS_HOST}:5000/v3/" \
	--bootstrap-public-url "http://${OS_HOST}:5000/v3/" \
	--bootstrap-region-id "${OS_REGION}"

systemctl status keystone-public || systemd-run --unit keystone-public -- \
	/opt/keystone/bin/keystone-wsgi-public --port 5000

cat <<EOS >/adminrc
export OS_USERNAME=admin
export OS_PASSWORD=${OS_ADMIN_PASS}
export OS_PROJECT_NAME=admin
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
export OS_AUTH_URL=http://localhost:5000/v3
export OS_IDENTITY_API_VERSION=3
EOS

source /adminrc

timeout 5 bash -c 'until openstack token issue; do sleep 1; done'

openstack project show service || openstack project create --domain default --description "Service Project" service
openstack user show "${OS_SERVICE_USER}" || openstack user create --domain default --password "${OS_SERVICE_PASS}" "${OS_SERVICE_USER}"
openstack role add --project service --user "${OS_SERVICE_USER}" admin
