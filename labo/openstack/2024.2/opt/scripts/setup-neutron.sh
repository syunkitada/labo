#!/bin/bash -xe

source /opt/openstack/envrc

SERVICE_NAME="neutron"
VENV_DIR=${VENV_DIR:-"/opt/${SERVICE_NAME}"}

useradd "${SERVICE_NAME}" || echo "ignore because the user already exists"

python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install -U pip

mkdir -p "$VENV_DIR/src"
mkdir -p /etc/neutron
mkdir -p /etc/neutron/plugins/ml2
mkdir -p /var/lib/neutron
mkdir -p /var/log/neutron

cd "$VENV_DIR/src"
if test -e neutron; then
	cd neutron
	git pull
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/neutron.git
	cd neutron
fi

"${VENV_DIR}/bin/pip" install . \
	-c "/opt/oscommon/src/requirements/upper-constraints.txt" \
	-r requirements.txt \
	-r /opt/openstack/neutron/requirements.txt

cp etc/api-paste.ini /etc/neutron/

cp /opt/openstack/neutron/rootwrap.conf /etc/neutron/rootwrap.conf
cp /opt/openstack/neutron/neutron.conf /etc/neutron/neutron.conf
cp /opt/openstack/neutron/ml2_conf.ini /etc/neutron/plugins/ml2/ml2_conf.ini

/opt/neutron/bin/neutron-db-manage --config-file /etc/neutron/neutron.conf \
	--config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head

systemctl reset-failed neutron-server || echo 'ignored'
systemctl status neutron-server || systemd-run \
	--unit neutron-server -- \
	/opt/neutron/bin/neutron-server \
	--config-file /etc/neutron/neutron.conf \
	--config-file /etc/neutron/plugins/ml2/ml2_conf.ini
systemctl restart neutron-server

service_list=$(openstack service list -f value -c 'Type')
if ! echo "$service_list" | grep -q network; then
	openstack service create --name neutron --description "OpenStack Network" network
	openstack endpoint create --region region1 network public http://localhost:9696
	openstack endpoint create --region region1 network internal http://localhost:9696
	openstack endpoint create --region region1 network admin http://localhost:9696
fi
