#!/bin/bash -xe

if [ $# != 1 ]; then
    echo "ERROR: Input node_host"
    echo "./41_setup_kubelet.sh [node_host]"
    exit 1
fi
NODE_HOST=$1

sudo yum install -y socat conntrack ipset

# By default the kubelet will fail to start if swap is enabled.
sudo swapoff -a


if [ ! -e /usr/local/bin/crictl ]; then
    wget "https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.21.0/crictl-v1.21.0-linux-amd64.tar.gz"
    tar -xvf crictl-v1.21.0-linux-amd64.tar.gz
    chmod +x crictl
    sudo mv crictl /usr/local/bin/
fi

if [ ! -e /opt/cni ]; then
    wget "https://github.com/containernetworking/plugins/releases/download/v0.9.1/cni-plugins-linux-amd64-v0.9.1.tgz"
    sudo mkdir -p \
      /etc/cni/net.d \
      /opt/cni/bin
    sudo tar -xvf cni-plugins-linux-amd64-v0.9.1.tgz -C /opt/cni/bin/
fi

if [ ! -e /usr/local/bin/kubectl ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v1.21.0/bin/linux/amd64/kubectl
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
fi

if [ ! -e /usr/local/bin/kube-proxy ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v1.21.0/bin/linux/amd64/kube-proxy
    chmod +x kube-proxy
    sudo mv kube-proxy /usr/local/bin/
fi


if [ ! -e /usr/local/bin/kubelet ]; then
    wget https://storage.googleapis.com/kubernetes-release/release/v1.21.0/bin/linux/amd64/kubelet
    chmod +x kubelet
    sudo mv kubelet /usr/local/bin/
fi

sudo mkdir -p \
  /var/lib/kubelet \
  /var/lib/kube-proxy \
  /var/lib/kubernetes \
  /var/run/kubernetes


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

cd ~/k8s-assets
sudo cp ${NODE_HOST}-key.pem ${NODE_HOST}.pem /var/lib/kubelet/
sudo cp ${NODE_HOST}.kubeconfig /var/lib/kubelet/kubeconfig
sudo cp ca.pem /var/lib/kubernetes/

cat <<EOF | sudo tee /var/lib/kubelet/kubelet-config.yaml
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: "/var/lib/kubernetes/ca.pem"
authorization:
  mode: Webhook
clusterDomain: "cluster.local"
clusterDNS:
  - "10.32.0.10"
podCIDR: "${POD_CIDR}"
resolvConf: "/etc/resolv.conf"
runtimeRequestTimeout: "15m"
tlsCertFile: "/var/lib/kubelet/${NODE_HOST}.pem"
tlsPrivateKeyFile: "/var/lib/kubelet/${NODE_HOST}-key.pem"
EOF

cat <<EOF | sudo tee /etc/systemd/system/kubelet.service
[Unit]
Description=Kubernetes Kubelet
Documentation=https://github.com/kubernetes/kubernetes
After=containerd.service
Requires=containerd.service

[Service]
ExecStart=/usr/local/bin/kubelet \\
  --config=/var/lib/kubelet/kubelet-config.yaml \\
  --container-runtime=remote \\
  --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock \\
  --image-pull-progress-deadline=2m \\
  --kubeconfig=/var/lib/kubelet/kubeconfig \\
  --network-plugin=cni \\
  --register-node=true \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure the Kubernetes Proxy
sudo cp kube-proxy.kubeconfig /var/lib/kube-proxy/kubeconfig
cat <<EOF | sudo tee /var/lib/kube-proxy/kube-proxy-config.yaml
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
clientConnection:
  kubeconfig: "/var/lib/kube-proxy/kubeconfig"
mode: "iptables"
clusterCIDR: "10.200.0.0/16"
EOF

cat <<EOF | sudo tee /etc/systemd/system/kube-proxy.service
[Unit]
Description=Kubernetes Kube Proxy
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-proxy \\
  --config=/var/lib/kube-proxy/kube-proxy-config.yaml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF


sudo systemctl daemon-reload
sudo systemctl enable kubelet kube-proxy
sudo systemctl start kubelet kube-proxy
