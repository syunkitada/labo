#!/bin/bash -x

source envrc

cd $K8S_ASSETS_DIR
cp kube-controller-manager.kubeconfig $VAR_DIR
cd -

for pid in `ps ax | grep controller-manager | grep -v .sh | awk '{print $1}'`
do
    kill $pid
done

cd $SRC_DIR
go run -mod vendor cmd/kube-controller-manager/controller-manager.go \
  --bind-address=0.0.0.0 \
  --cluster-cidr=10.200.0.0/16 \
  --cluster-name=kubernetes \
  --cluster-signing-cert-file=${VAR_DIR}/ca.pem \
  --cluster-signing-key-file=${VAR_DIR}/ca-key.pem \
  --kubeconfig=${VAR_DIR}/kube-controller-manager.kubeconfig \
  --leader-elect=true \
  --root-ca-file=${VAR_DIR}/ca.pem \
  --service-account-private-key-file=/${VAR_DIR}/service-account-key.pem \
  --service-cluster-ip-range=10.32.0.0/24 \
  --use-service-account-credentials=true \
  --v=2 \
  1>$LOG_DIR/kube-controller-manager.log 2>&1 &
