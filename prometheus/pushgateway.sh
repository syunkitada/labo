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

if echo $PWD | grep 'setup-scripts/prometheus'; then
   cd ../
fi

function start() {
    ymlPath="${PWD}/prometheus/etc/pushgateway.yml"
    # -v ${ymlPath}:/etc/pushgateway/pushgateway.yml \
    sudo docker ps | grep " pushgateway$" || \
        ( \
            ((sudo docker ps --all | grep " pushgateway$" && sudo docker rm pushgateway) || echo "pushgateway not found") && \
            sudo docker run --name pushgateway -d \
            --net="host" \
            prom/pushgateway \
        )
}

function stop() {
    sudo docker ps | grep " pushgateway$" && sudo docker kill pushgateway || echo "pushgateway not found"
}

function restart() {
    stop
    start
}

$COMMAND
