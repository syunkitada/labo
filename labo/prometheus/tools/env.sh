#!/bin/sh -e

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/prometheus/tools"}'`

sudo apt install -y jq

mkdir -p ~/.setup-scripts/prometheus
cp $ROOT/metrics ~/.setup-scripts/prometheus/metrics
