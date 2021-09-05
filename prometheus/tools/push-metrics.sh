#!/bin/bash -e

COMMAND="${@:-help}"
PORT="${2:-9091}"


function push() {
    cat <<EOF | curl -v --data-binary @- http://127.0.0.1:${PORT}/metrics/job/push_job/instance/pusher1
# TYPE some_metric counter
check_pusher1{label1="val1"} 0
# TYPE another_metric gauge
# HELP another_metric Just an example.
check_pusher2{label1="val1"} 1
EOF
}


function delete() {
    curl -v -XDELETE http://127.0.0.1:${PORT}/metrics/job/push_job/instance/pusher1
}


$COMMAND
