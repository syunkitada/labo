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

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/prometheus/allinone"}'`

function _start() {
    name=prometheus
    port=$1
    ymlPath="${ROOT}/etc/${name}.yml"
    alertrulesYmlPath="${ROOT}/etc/alertrules.yml"
    sudo docker ps | grep " ${name}$" || \
        ( \
            ((sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name}) || echo "${name} not found") && \
            sudo docker run --name ${name} -d \
            --net="host" \
            -v ${ymlPath}:/etc/prometheus/prometheus.yml \
            -v ${alertrulesYmlPath}:/etc/prometheus/alertrules.yml \
            prom/prometheus \
            --web.listen-address=0.0.0.0:${port} \
            --config.file=/etc/prometheus/prometheus.yml \
            --storage.tsdb.path=/prometheus \
            --web.console.libraries=/usr/share/prometheus/console_libraries \
            --web.console.templates=/usr/share/prometheus/consoles \
        )
}

function _stop() {
    name=prometheus
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
}

function start() {
    _start 9090
}

function stop() {
    _stop
}

function restart() {
    stop
    start
}

$COMMAND
