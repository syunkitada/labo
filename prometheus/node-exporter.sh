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
    ymlPath="${PWD}/node-exporter/etc/node-exporter.yml"
    sudo docker ps | grep " node-exporter$" || \
        ( \
            ((sudo docker ps --all | grep " node-exporter$" && sudo docker rm node-exporter) || echo "node-exporter not found") && \
            sudo docker run --name node-exporter -d \
                --net="host" \
                --pid="host" \
                -v "/:/host:ro,rslave" \
                quay.io/prometheus/node-exporter:latest \
                --path.rootfs=/host \
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
