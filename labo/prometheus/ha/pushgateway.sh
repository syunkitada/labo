#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start pushgateway
./*.sh start

# stop pushgateway
./*.sh stop

# restart pushgateway
./*.sh restart
EOS
}

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/prometheus/ha"}'`

function _start() {
    name=pushgateway$1
    port=$2
    sudo docker ps | grep " ${name}$" || \
        ( \
            ((sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name}) || echo "${name} not found") && \
            sudo docker run --name ${name} -d \
            --net="host" \
            prom/pushgateway \
            --web.listen-address="0.0.0.0:${port}" \
        )
}

function _stop() {
    name=pushgateway$1
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
}

function start() {
    _start 1-1 9181
    _start 1-2 9182
}

function stop() {
    _stop 1-1
    _stop 1-2
}

function restart() {
    stop
    start
}

$COMMAND
