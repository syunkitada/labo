#!/bin/bash -xe

if [ -e /etc/labo/tls-assets/localhost.text ]; then
	exit 0
fi

sudo mkdir -p /etc/labo/tls-assets/localhost.test
cd /etc/labo/tls-assets/localhost.test

sudo sh -c "
cfssl gencert -config ../ca-config.json -initca ../ca-csr.json | cfssljson -bare ca
cfssl gencert \
	-ca=ca.pem \
	-ca-key=ca-key.pem \
	-config=../ca-config.json \
	-hostname=*.localhost.test \
	-profile=server \
	../server-csr.json | cfssljson -bare server
"
