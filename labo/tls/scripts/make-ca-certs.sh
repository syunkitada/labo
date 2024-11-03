#!/bin/bash -e

CA_CONFIG_PATH=${CA_CONFIG_PATH:-/etc/labo/tls-assets/ca/ca-config.json}
CA_CSR_PATH=${CA_CSR_PATH:-/etc/labo/tls-assets/ca/ca-csr.json}
CA_PEM_PATH=/etc/labo/tls-assets/ca/ca-certs/ca.pem

if test -e "${CA_PEM_PATH}"; then
	echo "SKIPPED: ca-certs is already initialized."
	exit 0
fi

sudo mkdir -p /etc/labo/tls-assets/ca

cat <<EOS | sudo tee "${CA_CONFIG_PATH}"
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "server": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
EOS

cat <<EOS | sudo tee "${CA_CSR_PATH}"
{
  "CN": "Labo",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "Labo",
      "OU": "CA",
      "ST": "Oregon"
    }
  ]
}
EOS

sudo mkdir -p /etc/labo/tls-assets/ca/ca-certs
cd /etc/labo/tls-assets/ca/ca-certs

# Generate ca
cfssl gencert -config "${CA_CONFIG_PATH}" -initca "${CA_CSR_PATH}" | sudo cfssljson -bare ca
