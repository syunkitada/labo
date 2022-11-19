#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start alertmanager
./*.sh start

# stop alertmanager
./*.sh stop

# restart alertmanager
./*.sh restart
EOS
}

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/prometheus/ha"}'`

function _start() {
    name=alertmanager$1
    port=$2
    clusterPort=$3
    peer=$4
    ymlPath="${ROOT}/etc/alertmanager.yml"
    storagePath="${HOME}/.setup-scripts/prometheus/ha/${name}"
    sudo docker ps | grep " ${name}$" || \
        ( \
            ((sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name}) || echo "${name} not found") && \
            sudo docker run --name ${name} -d \
            --user root \
            --net="host" \
            -v ${ymlPath}:/etc/alertmanager/alertmanager.yml \
            -v ${storagePath}:/var/lib/alertmanager \
            prom/alertmanager \
            --config.file=/etc/alertmanager/alertmanager.yml \
            --storage.path=/var/lib/alertmanager \
            --web.listen-address=0.0.0.0:${port} \
            --cluster.listen-address=0.0.0.0:${clusterPort} \
            ${peer} \
        )
}

function _stop() {
    name=alertmanager$1
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
}

function start() {
    _start 1-1 9193 9194 "--cluster.peer=127.0.0.1:9294 --cluster.peer=127.0.0.1:9394"
    _start 1-2 9293 9294 "--cluster.peer=127.0.0.1:9194 --cluster.peer=127.0.0.1:9394"
    _start 1-3 9393 9394 "--cluster.peer=127.0.0.1:9194 --cluster.peer=127.0.0.1:9294"
}

function stop() {
    _stop 1-1
    _stop 1-2
    _stop 1-3
}

function restart() {
    stop
    start
}

$COMMAND
