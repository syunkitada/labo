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

NAME="alertmanager2"

function start() {
    ymlPath="${PWD}/prometheus/etc/alertmanager.yml"
    sudo docker ps | grep " ${NAME}$" || \
        ( \
            ((sudo docker ps --all | grep " ${NAME}$" && sudo docker rm ${NAME}) || echo "${NAME} not found") && \
            sudo docker run --name ${NAME} -d \
            --net="host" \
            -v ${ymlPath}:/etc/alertmanager/alertmanager.yml \
            prom/alertmanager \
            --config.file=/etc/alertmanager/alertmanager.yml \
            --storage.path=/alertmanager \
            --web.listen-address=0.0.0.0:9293 \
            --cluster.listen-address=0.0.0.0:9294 \
            --cluster.peer=127.0.0.1:9194 \
            --cluster.peer=127.0.0.1:9394 \
        )
}

function stop() {
    sudo docker ps | grep " ${NAME}$" && sudo docker kill ${NAME} || echo "${NAME} not found"
}

function restart() {
    stop
    start
}

$COMMAND
