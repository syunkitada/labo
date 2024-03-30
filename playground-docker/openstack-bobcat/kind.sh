#!/bin/bash -ex

IP_ADDR=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-worker)
labo-record-ctl delete *.ingress.kind.test
labo-record-ctl create test *.ingress.kind.test a ${IP_ADDR}

sudo docker exec -i openstack-bobcat-ansible mkdir -p /root/.kube/
sudo kind get kubeconfig -n kind | sed -e 's|server: .*|server: https://kind-control-plane:6443|g' | sudo docker exec -i openstack-bobcat-ansible tee /root/.kube/config

# $ kind export -n kind kubeconfig
# $ kind delete cluster -n openstack-bobcat
