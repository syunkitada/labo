#!/bin/bash -xe

if [ $# != 2 ]; then
    echo "ERROR: Input node_ip"
    echo "./10_setup_cfgs.sh [node_host] [node_ip]"
    exit 1
fi

NODE_HOST=$1
NODE_IP=$2
API_IP=${NODE_IP}
mkdir -p ~/k8s-assets
cd ~/k8s-assets

# CA(Certificate Authority: 認証局)を作成する
# CAの秘密鍵は、証明書を発行する際の電子署名に利用される
# 証明書のCNは、ユーザ名として利用される
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


# adminユーザ用のクライアント証明書を作成する
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


# kubelet用のクライアント証明書を作成する
# kubernetes-apiserverは、kubeletからのリクエストを認証するNode Authorizerとよばれる認証モードを使用する
# Node Authorizerによって認証されるためには、kubeletはsystem:nodes system:node:<nodeName>のユーザ名でsystem:nodesグループ内に存在することを示す証明書を利用する必要がある
# xxx-key.pem, xxx.pem
if [ ! -e ${NODE_HOST}.pem ] || [ ! -e ${NODE_HOST}-key.pem ] || [ ! -e ${NODE_HOST}.csr ]; then
cat > ${NODE_HOST}-csr.json <<EOF
{
  "CN": "system:node:${NODE_HOST}",
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
  -hostname=${NODE_HOST},${NODE_IP} \
  -profile=kubernetes \
  ${NODE_HOST}-csr.json | cfssljson -bare ${NODE_HOST}
fi


# kube-controller-manager用のクライアント証明書を作成する
# kube-controller-manager-key.pem, kube-controller-manager-key.pem
if [ ! -e kube-controller-manager.pem ] || [ ! -e kube-controller-manager-key.pem ] || [ ! -e kube-controller-manager.csr ]; then
cat > kube-controller-manager-csr.json <<EOF
{
  "CN": "system:kube-controller-manager",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "L": "Portland",
      "O": "system:kube-controller-manager",
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
  kube-controller-manager-csr.json | cfssljson -bare kube-controller-manager
fi


# kube-proxy用のクライアント証明書を作成する
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


# kube-scheduler用のクライアント証明書を作成する
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


# kube-api-server用の証明書を作成する
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

KUBERNETES_HOSTNAMES=kubernetes,kubernetes.default,kubernetes.default.svc,kubernetes.default.svc.cluster,kubernetes.svc.cluster.local

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -hostname=10.32.0.1,10.240.0.10,10.240.0.11,10.240.0.12,${API_IP},127.0.0.1,${KUBERNETES_HOSTNAMES} \
  -profile=kubernetes \
  kubernetes-csr.json | cfssljson -bare kubernetes
fi


# サービスアカウントのキーペア(証明書と秘密鍵)を生成する
# キーペアは、Controller Managerで稼働するToken ControllerがService Account Tokenを生成するためのもの
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



# ---------------------------------------------
# Create kubernetes configs
# ---------------------------------------------

# k8sの各サービスが使用するkubeconfigを作成する

# kubelet用のkubeconfigを作成する
kubectl config set-cluster kubernetes-the-hard-way \
  --certificate-authority=ca.pem \
  --embed-certs=true \
  --server=https://${API_IP}:6443 \
  --kubeconfig=${NODE_HOST}.kubeconfig

kubectl config set-credentials system:node:${NODE_HOST} \
  --client-certificate=${NODE_HOST}.pem \
  --client-key=${NODE_HOST}-key.pem \
  --embed-certs=true \
  --kubeconfig=${NODE_HOST}.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes-the-hard-way \
  --user=system:node:${NODE_HOST} \
  --kubeconfig=${NODE_HOST}.kubeconfig

kubectl config use-context default --kubeconfig=${NODE_HOST}.kubeconfig


# kube-proxy用のkubeconfigを作成する
kubectl config set-cluster kubernetes-the-hard-way \
    --certificate-authority=ca.pem \
    --embed-certs=true \
    --server=https://${API_IP}:6443 \
    --kubeconfig=kube-proxy.kubeconfig

kubectl config set-credentials system:kube-proxy \
    --client-certificate=kube-proxy.pem \
    --client-key=kube-proxy-key.pem \
    --embed-certs=true \
    --kubeconfig=kube-proxy.kubeconfig

kubectl config set-context default \
    --cluster=kubernetes-the-hard-way \
    --user=system:kube-proxy \
    --kubeconfig=kube-proxy.kubeconfig

kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig


# kube-controller-manager用のkubeconfigを作成する
kubectl config set-cluster kubernetes-the-hard-way \
    --certificate-authority=ca.pem \
    --embed-certs=true \
    --server=https://127.0.0.1:6443 \
    --kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-credentials system:kube-controller-manager \
    --client-certificate=kube-controller-manager.pem \
    --client-key=kube-controller-manager-key.pem \
    --embed-certs=true \
    --kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-context default \
    --cluster=kubernetes-the-hard-way \
    --user=system:kube-controller-manager \
    --kubeconfig=kube-controller-manager.kubeconfig

kubectl config use-context default --kubeconfig=kube-controller-manager.kubeconfig


# kube-scheduler用のkubeconfigを作成する
kubectl config set-cluster kubernetes-the-hard-way \
    --certificate-authority=ca.pem \
    --embed-certs=true \
    --server=https://127.0.0.1:6443 \
    --kubeconfig=kube-scheduler.kubeconfig

kubectl config set-credentials system:kube-scheduler \
    --client-certificate=kube-scheduler.pem \
    --client-key=kube-scheduler-key.pem \
    --embed-certs=true \
    --kubeconfig=kube-scheduler.kubeconfig

kubectl config set-context default \
    --cluster=kubernetes-the-hard-way \
    --user=system:kube-scheduler \
    --kubeconfig=kube-scheduler.kubeconfig

kubectl config use-context default --kubeconfig=kube-scheduler.kubeconfig


# adminユーザ用のkubeconfig
kubectl config set-cluster kubernetes-the-hard-way \
  --certificate-authority=ca.pem \
  --embed-certs=true \
  --server=https://127.0.0.1:6443 \
  --kubeconfig=admin.kubeconfig

kubectl config set-credentials admin \
  --client-certificate=admin.pem \
  --client-key=admin-key.pem \
  --embed-certs=true \
  --kubeconfig=admin.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes-the-hard-way \
  --user=admin \
  --kubeconfig=admin.kubeconfig

kubectl config use-context default --kubeconfig=admin.kubeconfig



# Secretを暗号化するための鍵と設定ファイルを作成する
if [ ! -e encryption-config.yaml ]; then
ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
cat > encryption-config.yaml <<EOF
kind: EncryptionConfig
apiVersion: v1
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF
fi
