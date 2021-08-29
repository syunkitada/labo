#!/bin/bash -ex

COMMAND="${@:-help}"

PORT=9980

function help() {
    cat << EOS
# start
./*.sh start
EOS
}

function fire() {
    startsAt=`date --date '3 minutes ago' "+%Y-%m-%dT%H:%M:%S.%N+09:00"`
    endsAt=`date --date '3 minutes' "+%Y-%m-%dT%H:%M:%S.%N+09:00"`
    json=`cat << EOS | jq -c .
[
  {
    "annotations":{"summary":"check4 alert summary"},
    "endsAt":"${endsAt}",
    "startsAt":"${startsAt}",
    "generatorURL":"http://owner-desktop:9090/graph?g0.expr=check4%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1",
    "labels":{"alertname":"check4","instance":"localhost:9980","job":"myjob","output":"criticalout","severity":"critical"}
  }
]
EOS`

    curl -v -XPOST -H 'Content-Type: application/json' localhost:9093/api/v2/alerts -d "$json"
}



function resolve() {
    startsAt=`date --date '3 minutes ago' "+%Y-%m-%dT%H:%M:%S.%N+09:00"`
    endsAt=`date --date '1 minutes ago' "+%Y-%m-%dT%H:%M:%S.%N+09:00"`
    json=`cat << EOS | jq -c .
[
  {
    "annotations":{"summary":"check4 alert summary"},
    "endsAt":"${endsAt}",
    "startsAt":"${startsAt}",
    "generatorURL":"http://owner-desktop:9090/graph?g0.expr=check4%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1",
    "labels":{"alertname":"check4","instance":"localhost:9980","job":"myjob","output":"criticalout","severity":"critical"}
  }
]
EOS`

    curl -XPOST -H 'Content-Type: application/json' localhost:9093/api/v2/alerts -d "$json"
}


$COMMAND
