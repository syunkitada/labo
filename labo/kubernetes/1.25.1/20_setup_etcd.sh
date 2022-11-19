#!/bin/bash -xe

source envrc

if [ $# != 2 ]; then
    echo "ERROR: Input node_ip"
    echo "./10_setup_cfgs.sh [etcd_name] [node_ip]"
    exit 1
fi
ETCD_NAME=$1
NODE_IP=$2

if [ ! -e ${BIN_DIR}/etcd ]; then
    cd /tmp
    wget "https://github.com/etcd-io/etcd/releases/download/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-amd64.tar.gz"
    tar -xvf etcd-${ETCD_VERSION}-linux-amd64.tar.gz
    mv etcd-${ETCD_VERSION}-linux-amd64/etcd* ${BIN_DIR}
    rm -rf etcd-${ETCD_VERSION}-linux-amd64.tar.gz
    cd -
fi

mkdir -p $ROOT_DIR/etc/etcd $ROOT_DIR/var/lib/etcd
chmod 700 $ROOT_DIR/var/lib/etcd
cp $K8S_ASSETS_DIR/ca.pem $K8S_ASSETS_DIR/kubernetes-key.pem $K8S_ASSETS_DIR/kubernetes.pem $ROOT_DIR/etc/etcd/

sudo docker ps | grep " etcd$" || \
sudo docker run -d -v $ROOT_DIR/etc/etcd:/etc/etcd -v $ROOT_DIR/var/lib/etcd:/var/lib/etcd --net host --rm \
 --name etcd quay.io/coreos/etcd:${ETCD_VERSION} \
  etcd \
  --name ${ETCD_NAME} \
  --cert-file=/etc/etcd/kubernetes.pem \
  --key-file=/etc/etcd/kubernetes-key.pem \
  --peer-cert-file=/etc/etcd/kubernetes.pem \
  --peer-key-file=/etc/etcd/kubernetes-key.pem \
  --trusted-ca-file=/etc/etcd/ca.pem \
  --peer-trusted-ca-file=/etc/etcd/ca.pem \
  --peer-client-cert-auth \
  --client-cert-auth \
  --initial-advertise-peer-urls https://${NODE_IP}:2380 \
  --listen-peer-urls https://${NODE_IP}:2380 \
  --listen-client-urls https://${NODE_IP}:2379,https://127.0.0.1:2379 \
  --advertise-client-urls https://${NODE_IP}:2379 \
  --initial-cluster-token etcd-cluster-0 \
  --initial-cluster ${ETCD_NAME}=https://${NODE_IP}:2380 \
  --initial-cluster-state new \
  --data-dir=/var/lib/etcd


ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=$ROOT_DIR/etc/etcd/ca.pem \
  --cert=$ROOT_DIR/etc/etcd/kubernetes.pem \
  --key=$ROOT_DIR/etc/etcd/kubernetes-key.pem
