#!/bin/bash -e

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start vm
./*.sh start
EOS
}

if echo $PWD | grep "/setup-scripts"; then
    cd `echo $PWD | awk -F '/setup-scripts' '{print $1}'`
fi

function start() {
    go run setup-scripts/nfs/watch.go --watch > /tmp/watch.log &
}

function status() {
    ps ax | grep watch.go
}

$COMMAND
