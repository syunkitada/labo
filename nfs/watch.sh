#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start vm
./*.sh start
EOS
}

if echo $PWD | grep "setup-scripts$"; then
    cd ../
fi

function start() {
    go run setup-scripts/nfs/watch.go --watch
}

$COMMAND
