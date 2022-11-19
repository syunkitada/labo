#!/bin/bash -xe

source envrc

kubectl apply -f resources/coredns-1.8.yaml
