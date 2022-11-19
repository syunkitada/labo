#!/bin/bash

source envrc

echo "
----------------------------------------------------------------------------------------------------
# etcd
"
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=$ROOT_DIR/etc/etcd/ca.pem \
  --cert=$ROOT_DIR/etc/etcd/kubernetes.pem \
  --key=$ROOT_DIR/etc/etcd/kubernetes-key.pem

echo "
----------------------------------------------------------------------------------------------------
# apiserver
"
ps ax | grep apiserver.g[o]

echo "
----------------------------------------------------------------------------------------------------
# controller-manager
"
ps ax | grep controller-manager.g[o]

echo "
----------------------------------------------------------------------------------------------------
# scheduler
"
ps ax | grep scheduler.g[o]

echo "
----------------------------------------------------------------------------------------------------
# kubelet
"
ps ax | grep kubelet.g[o] | grep -v sudo

echo "
----------------------------------------------------------------------------------------------------
# kube-proxy
"
ps ax | grep proxy.g[o] | grep -v sudo


echo "
----------------------------------------------------------------------------------------------------
# resources
"
kubectl get pod --all-namespaces
