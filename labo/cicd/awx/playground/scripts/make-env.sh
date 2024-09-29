#!/bin/bash -ex

# ----------------------------------------------------------------------------------------------------
# Setup docker compose
sudo -E docker compose up -d

# ----------------------------------------------------------------------------------------------------
# Setup kind
cd "$(dirname "$0")/../" || exit 1

kind_clusters=$(sudo kind get clusters)
if ! echo "${kind_clusters}" | grep "^kind-awx$"; then
	sudo kind create cluster --config scripts/kind.yml
fi

kubeconfig=$(sudo kind get kubeconfig -n kind-awx)
echo "${kubeconfig}" >~/.kube/config

# ----------------------------------------------------------------------------------------------------
# Setup haproxy-ingress
INGRESS_WORKER=kind-awx-worker
DNS_RECORD="*.ingress.kind-awx.test"
IP_ADDR=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${INGRESS_WORKER})
labo-record-ctl delete "${DNS_RECORD}"
labo-record-ctl create test "${DNS_RECORD}" a "${IP_ADDR}"

# haproxy-ingress
# https://artifacthub.io/packages/helm/haproxy-ingress/haproxy-ingress
repo_list=$(sudo helm repo list)
echo "${repo_list}" | grep 'haproxy-ingress' || sudo helm repo add haproxy-ingress https://haproxy-ingress.github.io/charts
sudo helm upgrade -i -n haproxy-ingress --create-namespace \
	-f scripts/haproxy-ingress.values.yml \
	haproxy-ingress haproxy-ingress/haproxy-ingress

# ----------------------------------------------------------------------------------------------------
# Setup AWX
kubectl config set-context --current --namespace=awx

kubectl apply -k awx-operator

kubectl apply -f awx-cr
