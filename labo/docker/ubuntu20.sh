#!/bin/bash -xe

COMMAND="${@:-run}"

function run() {
    name=ubuntu20
    sudo docker ps | grep " ${name}$" || \
        ( \
            ((sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name}) || echo "${name} not found") && \
            sudo docker run --name ${name} -d \
            --net="host" \
            ubuntu:20.04 \
            sleep 36000 \
        )
}

$COMMAND
