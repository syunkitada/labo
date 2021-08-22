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

if echo $PWD | grep 'setup-scripts/prometheus'; then
   cd ../
fi

function start() {
    ymlPath="${PWD}/prometheus/etc/alertmanager.yml"
    sudo docker ps | grep " alertmanager$" || \
        ( \
            ((sudo docker ps --all | grep " alertmanager$" && sudo docker rm alertmanager) || echo "alertmanager not found") && \
            sudo docker run --name alertmanager -d \
            --net="host" \
            -v ${ymlPath}:/etc/alertmanager/alertmanager.yml \
            prom/alertmanager \
        )
}

function stop() {
    sudo docker ps | grep " prometheus$" && sudo docker kill alertmanager || echo "alertmanager not found"
}

function restart() {
    stop
    start
}

$COMMAND
