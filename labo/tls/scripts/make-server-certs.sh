#!/bin/bash -e

HOSTNAME_SUFFIX=${1:?}

CA_CONFIG_PATH=${CA_CONFIG_PATH:-/etc/labo/tls-assets/ca/ca-config.json}
CA_CSR_PATH=${CA_CSR_PATH:-/etc/labo/tls-assets/ca/ca-csr.json}
CA_PEM_PATH=/etc/labo/tls-assets/ca/ca-certs/ca.pem
CA_KEY_PATH=/etc/labo/tls-assets/ca/ca-certs/ca-key.pem

SERVER_CERTS_ROOT_DIR="/etc/labo/tls-assets/${HOSTNAME_SUFFIX}"
SERVER_CSR_PATH="${SERVER_CERTS_ROOT_DIR}/server-csr.json"

if test -e "${SERVER_CERTS_ROOT_DIR}"; then
	echo "SKIPPED: server-certs is already initialized."
	exit 0
fi

sudo mkdir -p "${SERVER_CERTS_ROOT_DIR}"

cat <<EOS | sudo tee "${SERVER_CSR_PATH}"
{
  "CN": "labo:server",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "labo:server",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOS

cd "${SERVER_CERTS_ROOT_DIR}"

sudo cfssl gencert \
	-ca="${CA_PEM_PATH}" \
	-ca-key="${CA_KEY_PATH}" \
	-config="${CA_CONFIG_PATH}" \
	-hostname="*.${HOSTNAME_SUFFIX}" \
	-profile=server \
	"${SERVER_CSR_PATH}" | sudo cfssljson -bare server
