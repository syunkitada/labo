#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start vm
./*.sh start
EOS
}

if echo $PWD | grep 'setup-scripts/prometheus'; then
   cd ../
fi

function start() {
    ymlPath="${PWD}/prometheus/etc/prometheus.yml"
    sudo docker ps | grep " prometheus$" || \
        ( \
            ((sudo docker ps --all | grep " prometheus$" && sudo docker rm prometheus) || echo "prometheus not found") && \
            sudo docker run -p 9090:9090 --name prometheus -d \
            -v ${ymlPath}:/etc/prometheus/prometheus.yml \
            prom/prometheus \
        )
}

function stop() {
    sudo docker ps | grep " prometheus$" && sudo docker kill prometheus || echo "prometheus not found"
}

function restart() {
    stop
    start
}

$COMMAND
