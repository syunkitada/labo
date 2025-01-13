#!/bin/bash -xe

source /opt/openstack/envrc

SERVICE_NAME="glance"
VENV_DIR=${VENV_DIR:-"/opt/${SERVICE_NAME}"}

useradd "${SERVICE_NAME}" || echo "ignore because the user already exists"

python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install -U pip

mkdir -p "$VENV_DIR/src"
mkdir -p "/etc/${SERVICE_NAME}"
mkdir -p "/var/log/${SERVICE_NAME}"

cd "$VENV_DIR/src"
if test -e glance; then
	cd glance
	git pull
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/glance.git
	cd glance
fi

"${VENV_DIR}/bin/pip" install . \
	-c "/opt/oscommon/src/requirements/upper-constraints.txt" \
	-r requirements.txt \
	-r /opt/openstack/glance/requirements.txt

cp etc/glance-api-paste.ini /etc/glance/
cp /opt/openstack/glance/glance-api.conf /etc/glance/glance-api.conf

/opt/glance/bin/glance-manage db_sync

systemctl reset-failed glance-api || echo 'ignored'
systemctl status glance-api || systemd-run \
	--unit glance-api -- \
	/opt/glance/bin/glance-api --config-file /etc/glance/glance-api.conf
systemctl restart glance-api

service_list=$(openstack service list -f value -c 'Type')
if ! echo "$service_list" | grep -q image; then
	openstack service create --name glance --description "OpenStack Image" image
	openstack endpoint create --region region1 image public http://localhost:9292
	openstack endpoint create --region region1 image internal http://localhost:9292
	openstack endpoint create --region region1 image admin http://localhost:9292
fi
