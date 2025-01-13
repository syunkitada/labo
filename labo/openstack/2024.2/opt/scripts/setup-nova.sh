#!/bin/bash -xe

source /opt/openstack/envrc

SERVICE_NAME="nova"
VENV_DIR=${VENV_DIR:-"/opt/${SERVICE_NAME}"}

useradd "${SERVICE_NAME}" || echo "ignore because the user already exists"

python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install -U pip

mkdir -p "$VENV_DIR/src"
cd "$VENV_DIR/src"
if test -e nova; then
	cd nova
	git pull
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/nova.git
	cd nova
fi

"${VENV_DIR}/bin/pip" install . \
	-c "/opt/oscommon/src/requirements/upper-constraints.txt" \
	-r requirements.txt \
	-r /opt/openstack/nova/requirements.txt

mkdir -p /etc/nova
mkdir -p /var/log/nova
mkdir -p /var/lib/nova/instances

cp etc/nova/api-paste.ini /etc/nova/

cp /opt/openstack/nova/rootwrap.conf /etc/nova/rootwrap.conf
cp /opt/openstack/nova/nova.conf /etc/nova/nova.conf

/opt/nova/bin/nova-manage api_db sync
/opt/nova/bin/nova-manage cell_v2 map_cell0
/opt/nova/bin/nova-manage cell_v2 list_cells | grep ' cell1 ' || /opt/nova/bin/nova-manage cell_v2 create_cell --name=cell1 --verbose
/opt/nova/bin/nova-manage db sync

systemctl reset-failed nova-api || echo 'ignored'
systemctl status nova-api || systemd-run \
	--unit nova-api -- \
	/opt/nova/bin/nova-api --config-file /etc/nova/nova.conf
systemctl restart nova-api

systemctl reset-failed nova-scheduler || echo 'ignored'
systemctl status nova-scheduler || systemd-run \
	--unit nova-scheduler -- \
	/opt/nova/bin/nova-scheduler --config-file /etc/nova/nova.conf
systemctl restart nova-scheduler

systemctl reset-failed nova-conductor || echo 'ignored'
systemctl status nova-conductor || systemd-run \
	--unit nova-conductor -- \
	/opt/nova/bin/nova-conductor --config-file /etc/nova/nova.conf
systemctl restart nova-conductor

service_list=$(openstack service list -f value -c 'Type')
if ! echo "$service_list" | grep -q compute; then
	openstack service create --name nova --description "OpenStack Compute" compute
	openstack endpoint create --region region1 compute public http://localhost:8774/v2.1
	openstack endpoint create --region region1 compute internal http://localhost:8774/v2.1
	openstack endpoint create --region region1 compute admin http://localhost:8774/v2.1
fi
