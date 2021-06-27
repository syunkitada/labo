#!/bin/bash -xe

if [ $# != 1 ]; then
    echo "help: input node_ip"
    echo "./10_setup_cfgs.sh [node_ip]"
    exit 1
fi

NODE_IP=$1
API_IP=${NODE_IP}
mkdir ~/k8s-pems
cd ~/k8s-pems

# Create CA(Certificate Authority)
# ca-key.pem, ca.pem
if [ ! -e ca-key.pem ] || [ ! -e ca.pem ] || [ ! -e ca.csr ]; then
cat > ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "kubernetes": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
EOF

cat > ca-csr.json <<EOF
{
  "CN": "Kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "Kubernetes",
      "OU": "CA",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert -initca ca-csr.json | cfssljson -bare ca
fi


# Create The Admin Client Certificate
# admin-key.pem, admin.pem
if [ ! -e admin-key.pem ] || [ ! -e admin.csr ] || [ ! -e admin.pem ]; then
cat > admin-csr.json <<EOF
{
  "CN": "admin",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:masters",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  admin-csr.json | cfssljson -bare admin
fi


# Create The Kubelet Client Certificates
# Kubernetes uses a special-purpose authorization mode called Node Authorizer, that specifically authorizes API requests made by Kubelets. In order to be authorized by the Node Authorizer, Kubelets must use a credential that identifies them as being in the system:nodes group, with a username of system:node:<nodeName>. In this section you will create a certificate for each Kubernetes worker node that meets the Node Authorizer requirements.
# xxx-key.pem, xxx.pem
if [ ! -e ${NODE_IP}.pem ] || [ ! -e ${NODE_IP}-key.pem ] || [ ! -e ${NODE_IP}.csr ]; then
cat > ${NODE_IP}-csr.json <<EOF
{
  "CN": "system:node:${NODE_IP}",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:nodes",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -hostname=${NODE_IP} \
  -profile=kubernetes \
  ${NODE_IP}-csr.json | cfssljson -bare ${NODE_IP}
fi



# The Controller Manager Client Certificate
# kube-proxy-key.pem, kube-proxy.pem
if [ ! -e kube-proxy.pem ] || [ ! -e kube-proxy-key.pem ] || [ ! -e kube-proxy.csr ]; then
cat > kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:kube-proxy",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-proxy-csr.json | cfssljson -bare kube-proxy
fi


# Create The Kube Proxy Client Certificate
# kube-proxy-key.pem, kube-proxy.pem
if [ ! -e kube-proxy.pem ] || [ ! -e kube-proxy-key.pem ] || [ ! -e kube-proxy.csr ]; then
cat > kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:node-proxier",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-proxy-csr.json | cfssljson -bare kube-proxy
fi


# Create The Scheduler Client Certificate
# kube-scheduler-key.pem, kube-scheduler.pem
if [ ! -e kube-scheduler.pem ] || [ ! -e kube-scheduler-key.pem ] || [ ! -e kube-scheduler.csr ]; then
cat > kube-scheduler-csr.json <<EOF
{
  "CN": "system:kube-scheduler",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:kube-scheduler",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  kube-scheduler-csr.json | cfssljson -bare kube-scheduler
fi


# Create The Kubernetes API Server Certificate
# kubernetes-key.pem, kubernetes.pem
if [ ! -e kubernetes.pem ] || [ ! -e kubernetes-key.pem ] || [ ! -e kubernetes.csr ]; then
cat > kubernetes-csr.json <<EOF
{
  "CN": "kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "Kubernetes",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -hostname=10.32.0.1,10.240.0.10,10.240.0.11,10.240.0.12,${API_IP},127.0.0.1 \
  -profile=kubernetes \
  kubernetes-csr.json | cfssljson -bare kubernetes
fi


# The Service Account Key Pair
# service-account-key.pem, service-account.pem
if [ ! -e service-account.pem ] || [ ! -e service-account-key.pem ] || [ ! -e service-account.csr ]; then
cat > service-account-csr.json <<EOF
{
  "CN": "service-accounts",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "Kubernetes",
      "OU": "Kubernetes The Hard Way",
      "ST": "Oregon"
    }
  ]
}
EOF

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=kubernetes \
  service-account-csr.json | cfssljson -bare service-account
fi
