#!/bin/bash -xe

sudo mkdir -p /etc/systemd/resolved.conf.d
sudo cp ./scripts/resolv-labo.conf /etc/systemd/resolved.conf.d/resolv-labo.conf

sudo systemctl restart systemd-resolved
