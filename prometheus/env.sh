#!/bin/sh -e

sudo apt install -y jq

mkdir -p ~/.setup-scripts/prometheus
cp etc/metrics ~/.setup-scripts/prometheus/metrics
