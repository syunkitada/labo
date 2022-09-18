#!/bin/bash -x

source envrc

if [ $# != 1 ]; then
    echo "ERROR: Input node_host"
    echo "./41_setup_kubelet.sh [node_host]"
    exit 1
fi
NODE_HOST=$1

sudo apt install -y socat conntrack ipset

# By default the kubelet will fail to start if swap is enabled.
sudo swapoff -a


if [ ! -e ${BIN_DIR}/crictl ]; then
    cd /tmp
    wget "https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.21.0/crictl-v1.21.0-linux-amd64.tar.gz"
    tar -xvf crictl-v1.21.0-linux-amd64.tar.gz
    chmod +x crictl
    mv crictl $BIN_DIR
    cd -
fi

if [ ! -e /opt/cni ]; then
    cd /tmp
    wget "https://github.com/containernetworking/plugins/releases/download/v0.9.1/cni-plugins-linux-amd64-v0.9.1.tgz"
    sudo mkdir -p \
      /etc/cni/net.d \
      /opt/cni/bin
    sudo tar -xvf cni-plugins-linux-amd64-v0.9.1.tgz -C /opt/cni/bin/
    cd -
fi


POD_CIDR="10.0.0.0/16"
# Configure CNI Networking
if ! sudo ls /etc/cni/net.d | grep calico; then
    cat <<EOF | sudo tee /etc/cni/net.d/10-bridge.conf
{
    "cniVersion": "0.4.0",
    "name": "bridge",
    "type": "bridge",
    "bridge": "cnio0",
    "isGateway": true,
    "ipMasq": true,
    "ipam": {
        "type": "host-local",
        "ranges": [
          [{"subnet": "${POD_CIDR}"}]
        ],
        "routes": [{"dst": "0.0.0.0/0"}]
    }
}
EOF

    cat <<EOF | sudo tee /etc/cni/net.d/99-loopback.conf
{
    "cniVersion": "0.4.0",
    "name": "lo",
    "type": "loopback"
}
EOF
fi

cd $K8S_ASSETS_DIR
cp ${NODE_HOST}-key.pem ${NODE_HOST}.pem ${VAR_KUBELET_DIR}
cp ${NODE_HOST}.kubeconfig ${VAR_KUBELET_DIR}/kubeconfig
cp ca.pem ${VAR_DIR}
cd -

cat <<EOF | tee ${VAR_KUBELET_DIR}/kubelet-config.yaml
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: "${VAR_DIR}/ca.pem"
authorization:
  mode: Webhook
clusterDomain: "cluster.local"
clusterDNS:
  - "10.32.0.10"
podCIDR: "${POD_CIDR}"
resolvConf: "/etc/resolv.conf"
runtimeRequestTimeout: "15m"
tlsCertFile: "${VAR_KUBELET_DIR}/${NODE_HOST}.pem"
tlsPrivateKeyFile: "${VAR_KUBELET_DIR}/${NODE_HOST}-key.pem"
EOF

for pid in `ps ax | grep -v apiserver | grep kubele[t] | grep -v .sh | awk '{print $1}'`
do
    sudo kill $pid
done

cd $SRC_DIR
sudo -E /usr/local/go/bin/go run -mod vendor cmd/kubelet/kubelet.go \
  --config=${VAR_KUBELET_DIR}/kubelet-config.yaml \
  --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock \
  --kubeconfig=${VAR_KUBELET_DIR}/kubeconfig \
  --register-node=true \
  --v=2 \
  1>${LOG_DIR}/kubelet.log 2>&1 &
