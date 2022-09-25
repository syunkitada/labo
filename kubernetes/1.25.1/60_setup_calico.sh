#!/bin/bash -x

source envrc

# Install the Tigera Calico operator and custom resource definitions.

# applyすると、以下のエラーがでる
# kubectl apply -f resources/tigera-operator.yaml
# The CustomResourceDefinition "installations.operator.tigera.io" is invalid: metadata.annotations: Too long: must have at most 262144 bytes
# kubectl apply ではロールバックなどのために更新前のリソースファイルをmetadata.annotationsに自動的に格納してくれている。metadata.annotationsの容量制限は256KBであるため、本来容量上限が1MBのConfigMapやSecretでも256KBを超えるとkubectl apply では単純にデプロイできない

kubectl replace -f resources/tigera-operator.yaml || kubectl create -f resources/tigera-operator.yaml


until kubectl get pod -n tigera-operator | grep tigera-operator | grep Running
do
    sleep 1s
done

# Install Calico by creating the necessary custom resource.
kubectl apply -f resources/tigera-custom-resources.yaml


if sudo ls /etc/cni/net.d | grep bridge; then
    sudo rm -rf /etc/cni/net.d/10-bridge.conf
    sudo rm -rf /etc/cni/net.d/99-loopback.conf
fi


if [ ! -e ${BIN_DIR}/calicoctl ]; then
    cd /tmp
	curl -o calicoctl -O -L  "https://github.com/projectcalico/calicoctl/releases/download/v3.24.1/calicoctl"
    chmod +x calicoctl
    mv calicoctl ${BIN_DIR}
    cd -
fi

echo "
----------------------------------------------------------------------------------------------------
You should restart kubelet
----------------------------------------------------------------------------------------------------
"
