#!/bin/bash -x

source envrc

cd $K8S_ASSETS_DIR
cp kube-proxy.kubeconfig ${VAR_KUBE_PROXY_DIR}/kubeconfig
cd -


# Configure the Kubernetes Proxy
cat <<EOF | tee ${VAR_KUBE_PROXY_DIR}/kube-proxy-config.yaml
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
clientConnection:
  kubeconfig: "${VAR_KUBE_PROXY_DIR}/kubeconfig"
mode: "iptables"
clusterCIDR: "10.200.0.0/16"
EOF

for pid in `ps ax | grep kube | grep prox[y] | grep -v .sh | awk '{print $1}'`
do
    sudo kill $pid
done

cd $SRC_DIR
sudo -E /usr/local/go/bin/go run -mod vendor cmd/kube-proxy/proxy.go \
  --kubeconfig=${VAR_DIR}/kubeconfig \
  --config=${VAR_KUBE_PROXY_DIR}/kube-proxy-config.yaml \
  1>${LOG_DIR}/kube-proxy.log 2>&1 &
