#!/bin/bash -ex

cd "$(dirname "$0")/../" || exit 1

kind_clusters=$(sudo kind get clusters)
if ! echo "${kind_clusters}" | grep "^kind$"; then
	sudo kind create cluster --config scripts/kind.yml
fi

IP_ADDR=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-worker)
labo-record-ctl delete *.ingress.kind.test
labo-record-ctl create test *.ingress.kind.test a "${IP_ADDR}"

sudo docker exec -i openstack-bobcat-ansible mkdir -p /root/.kube/
kubeconfig=$(sudo kind get kubeconfig -n kind)
echo "${kubeconfig}" |
	sed -e 's|server: .*|server: https://kind-control-plane:6443|g' |
	sudo docker exec -i openstack-bobcat-ansible tee /root/.kube/config

sudo mkdir -p /etc/ansible/root/.kube
echo "${kubeconfig}" | sudo tee /etc/ansible/root/.kube/config
sudo sed -i 's|server: .*|server: https://kind-control-plane:6443|g' /etc/ansible/root/.kube/config

sudo helm repo add haproxy-ingress https://haproxy-ingress.github.io/charts
sudo helm upgrade -i ingress haproxy-ingress/haproxy-ingress

# echo $PWD
# sudo helm repo add bitnami https://charts.bitnami.com/bitnami
# sudo helm upgrade -i -n awx --create-namespace postgresql bitnami/postgresql -f scripts/postgresql.yml
#
# sudo helm repo add awx-operator https://ansible.github.io/awx-operator
# sudo helm upgrade -i -n awx --create-namespace awx-operator awx-operator/awx-operator

# sudo kubectl apply -f scripts/awx.yml
