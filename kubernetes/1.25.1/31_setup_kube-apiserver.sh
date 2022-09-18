#!/bin/bash -x

source envrc

if [ $# != 1 ]; then
    echo "ERROR: Input node_ip"
    echo "./31_setup_kube-apiserver.sh [node_ip]"
    exit 1
fi
NODE_IP=$1


cd $K8S_ASSETS_DIR
cp ca.pem ca-key.pem kubernetes-key.pem kubernetes.pem \
    service-account-key.pem service-account.pem \
    encryption-config.yaml $ROOT_DIR/var/lib/kubernetes/
cd -


for pid in `ps ax | grep apiserver | grep -v .sh | awk '{print $1}'`
do
    kill $pid
done

cd $SRC_DIR
go run -mod vendor cmd/kube-apiserver/apiserver.go \
  --advertise-address=${NODE_IP} \
  --allow-privileged=true \
  --apiserver-count=3 \
  --audit-log-maxage=30 \
  --audit-log-maxbackup=3 \
  --audit-log-maxsize=100 \
  --audit-log-path=${LOG_DIR}/audit.log \
  --authorization-mode=Node,RBAC \
  --bind-address=0.0.0.0 \
  --client-ca-file=${VAR_DIR}/ca.pem \
  --enable-admission-plugins=NamespaceLifecycle,NodeRestriction,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota \
  --etcd-cafile=${VAR_DIR}/ca.pem \
  --etcd-certfile=${VAR_DIR}/kubernetes.pem \
  --etcd-keyfile=${VAR_DIR}/kubernetes-key.pem \
  --etcd-servers=https://${NODE_IP}:2379 \
  --event-ttl=1h \
  --encryption-provider-config=${VAR_DIR}/encryption-config.yaml \
  --kubelet-certificate-authority=${VAR_DIR}/ca.pem \
  --kubelet-client-certificate=${VAR_DIR}/kubernetes.pem \
  --kubelet-client-key=${VAR_DIR}/kubernetes-key.pem \
  --service-account-key-file=${VAR_DIR}/service-account.pem \
  --service-account-signing-key-file=${VAR_DIR}/service-account-key.pem \
  --service-account-issuer=https://${NODE_IP}:6443 \
  --service-cluster-ip-range=10.32.0.0/24 \
  --service-node-port-range=30000-32767 \
  --tls-cert-file=${VAR_DIR}/kubernetes.pem \
  --tls-private-key-file=${VAR_DIR}/kubernetes-key.pem \
  --v=2 \
  1>$LOG_DIR/kube-apiserver.log 2>&1 &
