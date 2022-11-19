#!/bin/bash -xe

export KUBECONFIG=~/k8s-assets/admin.kubeconfig

# Install the Tigera Calico operator and custom resource definitions.
kubectl apply -f resources/tigera-operator.yaml


until kubectl get pod -n tigera-operator | grep tigera-operator | grep Running
do
    sleep 1s
done

# Install Calico by creating the necessary custom resource.
kubectl apply -f resources/tigera-custom-resources.yaml


if sudo ls /etc/cni/net.d | grep bridge; then
    sudo rm -rf /etc/cni/net.d/10-bridge.conf
    sudo rm -rf /etc/cni/net.d/99-loopback.conf
    sudo systemctl restart kubelet
fi


if [ ! -e /usr/bin/calicoctl ]; then
	curl -o calicoctl -O -L  "https://github.com/projectcalico/calicoctl/releases/download/v3.20.0/calicoctl"
    chmod +x calicoctl
    sudo mv calicoctl /usr/bin/
fi
