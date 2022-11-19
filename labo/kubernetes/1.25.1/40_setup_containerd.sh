#!/bin/bash -xe

source envrc

cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF


if [ ! -e /opt/containerd ]; then
    cd /tmp
    wget "https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-amd64.tar.gz"
    mkdir -p containerd
    tar -xvf containerd-${CONTAINERD_VERSION}-linux-amd64.tar.gz -C containerd
    sudo mv containerd/bin/* /bin/
    cd -
fi


if [ ! -e /usr/local/bin/runc ]; then
    wget "https://github.com/opencontainers/runc/releases/download/v1.0.0-rc93/runc.amd64"
    chmod +x runc.amd64
    sudo mv runc.amd64 /usr/local/bin/runc
fi

sudo mkdir -p /etc/containerd/

containerd config default | sudo tee /etc/containerd/config.toml

cat <<EOF | sudo tee /etc/systemd/system/containerd.service
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target

[Service]
ExecStartPre=/sbin/modprobe overlay
ExecStart=/bin/containerd
Restart=always
RestartSec=5
Delegate=yes
KillMode=process
OOMScoreAdjust=-999
LimitNOFILE=1048576
LimitNPROC=infinity
LimitCORE=infinity

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable containerd
sudo systemctl restart containerd
