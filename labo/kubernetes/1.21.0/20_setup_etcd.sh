#!/bin/bash -xe

if [ $# != 2 ]; then
    echo "ERROR: Input node_ip"
    echo "./10_setup_cfgs.sh [etcd_name] [node_ip]"
    exit 1
fi
ETCD_NAME=$1
NODE_IP=$2

if [ ! -e /usr/local/bin/etcd ]; then
    cd /tmp
    wget "https://github.com/etcd-io/etcd/releases/download/v3.4.15/etcd-v3.4.15-linux-amd64.tar.gz"
    tar -xvf etcd-v3.4.15-linux-amd64.tar.gz
    sudo mv etcd-v3.4.15-linux-amd64/etcd* /usr/local/bin/
    cd -
fi

sudo mkdir -p /etc/etcd /var/lib/etcd
sudo chmod 700 /var/lib/etcd
sudo cp ~/k8s-assets/ca.pem ~/k8s-assets/kubernetes-key.pem ~/k8s-assets/kubernetes.pem /etc/etcd/


cat <<EOF | sudo tee /etc/systemd/system/etcd.service
[Unit]
Description=etcd
Documentation=https://github.com/coreos

[Service]
Type=notify
ExecStart=/usr/local/bin/etcd \\
  --name ${ETCD_NAME} \\
  --cert-file=/etc/etcd/kubernetes.pem \\
  --key-file=/etc/etcd/kubernetes-key.pem \\
  --peer-cert-file=/etc/etcd/kubernetes.pem \\
  --peer-key-file=/etc/etcd/kubernetes-key.pem \\
  --trusted-ca-file=/etc/etcd/ca.pem \\
  --peer-trusted-ca-file=/etc/etcd/ca.pem \\
  --peer-client-cert-auth \\
  --client-cert-auth \\
  --initial-advertise-peer-urls https://${NODE_IP}:2380 \\
  --listen-peer-urls https://${NODE_IP}:2380 \\
  --listen-client-urls https://${NODE_IP}:2379,https://127.0.0.1:2379 \\
  --advertise-client-urls https://${NODE_IP}:2379 \\
  --initial-cluster-token etcd-cluster-0 \\
  --initial-cluster-state new \\
  --data-dir=/var/lib/etcd
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable etcd
sudo systemctl start etcd

sudo ETCDCTL_API=3 /usr/local/bin/etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/etcd/ca.pem \
  --cert=/etc/etcd/kubernetes.pem \
  --key=/etc/etcd/kubernetes-key.pem
