#!/bin/bash -xe

source envrc

cd /tmp

if [ ! -e /usr/local/bin/cfssl ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssl
    chmod +x cfssl
    mv cfssl ${BIN_DIR}
fi

if [ ! -e /usr/local/bin/cfssljson ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssljson
    chmod +x cfssljson
    mv cfssljson ${BIN_DIR}
fi

if [ ! -e /usr/local/bin/kubectl ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v1.21.0/bin/linux/amd64/kubectl
    chmod +x kubectl
    mv kubectl ${BIN_DIR}
fi
