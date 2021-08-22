#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start prometheus
./*.sh start

# stop prometheus
./*.sh stop

# restart prometheus
./*.sh restart
EOS
}

if echo $PWD | grep 'setup-scripts/prometheus'; then
   cd ../
fi

function start() {
    ymlPath="${PWD}/prometheus/etc/prometheus.yml"
    alertrulesYmlPath="${PWD}/prometheus/etc/alertrules.yml"
    sudo docker ps | grep " prometheus$" || \
        ( \
            ((sudo docker ps --all | grep " prometheus$" && sudo docker rm prometheus) || echo "prometheus not found") && \
            sudo docker run --name prometheus -d \
            --net="host" \
            -v ${ymlPath}:/etc/prometheus/prometheus.yml \
            -v ${alertrulesYmlPath}:/etc/prometheus/alertrules.yml \
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
