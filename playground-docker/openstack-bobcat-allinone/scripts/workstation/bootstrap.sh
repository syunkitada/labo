#!/bin/bash -xe

sudo dnf install -y podman podman-docker

cp /etc/ansible/scripts/workstation/registries.conf /etc/containers/registries.conf
