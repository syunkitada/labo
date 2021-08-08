#!/bin/bash -xe

export KUBECONFIG=~/k8s-assets/admin.kubeconfig

kubectl apply -f https://storage.googleapis.com/kubernetes-the-hard-way/coredns-1.8.yaml
