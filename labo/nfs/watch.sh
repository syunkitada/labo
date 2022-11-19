#!/bin/bash -e

COMMAND="${@:-start}"

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
    export GO111MODULE=off
    go get -u gopkg.in/godo.v2/cmd/godo
    /usr/loca/go/bin/go run setup-scripts/nfs/watch.go --watch > /tmp/watch.log &
}

function status() {
    ps ax | grep watch.go
}

$COMMAND
