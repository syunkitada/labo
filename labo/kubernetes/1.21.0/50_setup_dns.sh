#!/bin/bash -xe

export KUBECONFIG=~/k8s-assets/admin.kubeconfig

kubectl apply -f resources/coredns-1.8.yaml
