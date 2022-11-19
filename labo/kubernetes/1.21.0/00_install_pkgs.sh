#!/bin/bash -xe

sudo yum install -y wget

if [ ! -e /usr/local/bin/cfssl ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssl
    chmod +x cfssl
    sudo mv cfssl /usr/local/bin/
fi

if [ ! -e /usr/local/bin/cfssljson ]; then
    wget https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/1.4.1/linux/cfssljson
    chmod +x cfssljson
    sudo mv cfssljson /usr/local/bin/
fi

if [ ! -e /usr/local/bin/kubectl ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v1.21.0/bin/linux/amd64/kubectl
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
fi
