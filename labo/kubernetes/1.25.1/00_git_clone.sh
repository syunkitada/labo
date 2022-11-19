#!/bin/bash -xe

source envrc

mkdir -p $PJ_DIR
cd $PJ_DIR
test -e kubernetes || git clone https://github.com/kubernetes/kubernetes.git -b v${VERSION}


mkdir -p ${BIN_DIR}
mkdir -p $VAR_DIR
mkdir -p $ETC_DIR
mkdir -p $LOG_DIR
mkdir -p $VAR_KUBELET_DIR
mkdir -p $VAR_KUBE_PROXY_DIR
