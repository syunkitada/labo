#!/bin/bash -xe

source envrc

cd /tmp

if [ ! -e ${BIN_DIR}/cfssl ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssl
    chmod +x cfssl
    mv cfssl ${BIN_DIR}
fi

if [ ! -e ${BIN_DIR}/cfssljson ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssljson
    chmod +x cfssljson
    mv cfssljson ${BIN_DIR}
fi

if [ ! -e ${BIN_DIR}/kubectl ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/amd64/kubectl
    chmod +x kubectl
    mv kubectl ${BIN_DIR}
fi
