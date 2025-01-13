#!/bin/bash -xe

source /opt/openstack/envrc

SERVICE_NAME="keystone"
VENV_DIR=${VENV_DIR:-"/opt/${SERVICE_NAME}"}

useradd "${SERVICE_NAME}" || echo "ignore because the user already exists"

python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install -U pip

mkdir -p "$VENV_DIR/src"
mkdir -p "/etc/${SERVICE_NAME}"
mkdir -p "/var/log/${SERVICE_NAME}"

cd "$VENV_DIR/src"
if test -e keystone; then
	cd keystone
	git pull
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/keystone.git
	cd keystone
fi

"${VENV_DIR}/bin/pip" install . \
	-c "/opt/oscommon/src/requirements/upper-constraints.txt" \
	-r requirements.txt \
	-r /opt/openstack/keystone/requirements.txt

cp /opt/openstack/keystone/keystone.conf /etc/keystone/keystone.conf

/opt/keystone/bin/keystone-manage db_sync

/opt/keystone/bin/keystone-manage \
	fernet_setup --keystone-user keystone --keystone-group keystone

/opt/keystone/bin/keystone-manage \
	credential_setup --keystone-user keystone --keystone-group keystone

/opt/keystone/bin/keystone-manage \
	bootstrap --bootstrap-password "adminpass" \
	--bootstrap-admin-url "http://localhost:5000/v3/" \
	--bootstrap-internal-url "http://localhost:5000/v3/" \
	--bootstrap-public-url "http://localhost:5000/v3/" \
	--bootstrap-region-id "region1"

systemctl reset-failed keystone-public || echo 'ignored'
systemctl status keystone-public ||
	systemd-run --unit keystone-public -- \
		/opt/keystone/bin/keystone-wsgi-public --port 5000
systemctl restart keystone-public

until openstack token issue; do
	sleep 5
done

openstack project create --domain default --description "Service Project" service || echo "ignore because the project may already exists"
openstack user create --domain default service --password servicepass || echo "ignore because the user may already exists"
openstack role add --project service --user service service || echo "ignore because the role may be already added"
openstack role add --project service --user service admin || echo "ignore because the role may be already added"
