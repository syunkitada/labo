#!/bin/bash -e

COMMAND="${@:-help}"

PORT=9980

function help() {
    cat << EOS
# start
./*.sh start

# stop
./*.sh stop

# restart
./*.sh restart

# show status
./*.sh status
EOS
}

function start() {
    cd /tmp/
    python3 -m http.server ${PORT} &> /dev/null &
    echo "Started"
}

function stop() {
    cd /tmp/
    for pid in `ps ax | grep "[p]ython3 -m http.server ${PORT}" | awk '{print $1}'`
    do
        kill $pid
    done
    echo "Stopped"
}

function restart() {
    stop
    start
}

function status() {
    if ps ax | grep "[p]ython3 -m http.server ${PORT}"; then
        echo "Running"
    else
        echo "Stopped"
    fi
}

$COMMAND
