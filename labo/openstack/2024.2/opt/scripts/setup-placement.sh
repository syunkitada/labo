#!/bin/bash -xe

source /opt/openstack/envrc

SERVICE_NAME="placement"
VENV_DIR=${VENV_DIR:-"/opt/${SERVICE_NAME}"}

useradd "${SERVICE_NAME}" || echo "ignore because the user already exists"

python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install -U pip

mkdir -p "$VENV_DIR/src"
mkdir -p "/etc/${SERVICE_NAME}"
mkdir -p "/var/log/${SERVICE_NAME}"

cd "$VENV_DIR/src"
if test -e placement; then
	cd placement
	git pull
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/placement.git
	cd placement
fi

"${VENV_DIR}/bin/pip" install . \
	-c "/opt/oscommon/src/requirements/upper-constraints.txt" \
	-r requirements.txt \
	-r /opt/openstack/placement/requirements.txt

cp /opt/openstack/placement/placement.conf /etc/placement/placement.conf

/opt/placement/bin/placement-manage db sync

systemctl reset-failed placement-api || echo 'ignored'
systemctl status placement-api || systemd-run \
	--unit placement-api -- \
	/opt/placement/bin/placement-api --port 8778
systemctl restart placement-api

service_list=$(openstack service list -f value -c 'Type')
if ! echo "$service_list" | grep -q placement; then
	openstack service create --name placement --description "OpenStack placement" placement
	openstack endpoint create --region region1 placement public http://localhost:8778
	openstack endpoint create --region region1 placement internal http://localhost:8778
	openstack endpoint create --region region1 placement admin http://localhost:8778
fi
