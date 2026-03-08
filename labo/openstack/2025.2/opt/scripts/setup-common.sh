#!/bin/bash -xe

source /opt/openstack/envrc

VENV_DIR="/opt/oscommon"

python3.12 -m venv --system-site-packages "${VENV_DIR}"
export PATH="${VENV_DIR}/bin:${PATH}"
pip install -U pip

if test -e "/${VENV_DIR}/src/requirements"; then
	cd "/${VENV_DIR}/src/requirements"
	git pull
	cd -
else
	git clone -b "${OS_VERSION}" https://github.com/openstack/requirements.git "/opt/oscommon/src/requirements"
fi

pip install -c "/opt/oscommon/src/requirements/upper-constraints.txt" -r "/opt/openstack/common/requirements.txt"

test -e /usr/local/bin/openstack || ln -s /opt/oscommon/bin/openstack /usr/local/bin/openstack
