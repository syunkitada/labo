#!/bin/bash -xe

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start prometheus
./*.sh start

# stop prometheus
./*.sh stop

# restart prometheus
./*.sh restart
EOS
}

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/prometheus/ha"}'`

function _start() {
    name=prometheus-$1
    port=$2
    ymlPath="${ROOT}/etc/${name}.yml"
    alertrulesYmlPath="${ROOT}/etc/alertrules.yml"
    sudo docker ps | grep " ${name}$" || \
        ( \
            ((sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name}) || echo "${name} not found") && \
            sudo docker run --name ${name} -d \
            --net="host" \
            -v ${ymlPath}:/etc/prometheus/prometheus.yml \
            -v ${alertrulesYmlPath}:/etc/prometheus/alertrules.yml \
            prom/prometheus \
            --web.listen-address=0.0.0.0:${port} \
            --config.file=/etc/prometheus/prometheus.yml \
            --storage.tsdb.path=/prometheus \
            --web.console.libraries=/usr/share/prometheus/console_libraries \
            --web.console.templates=/usr/share/prometheus/consoles \
        )
}

function _stop() {
    name=prometheus-$1
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
}

function start-scraper() {
    _start "scraper1-1" 9191
    _start "scraper1-2" 9192
    _start "scraper2-1" 9291
    _start "scraper2-2" 9292
}

function stop-scraper() {
    _stop "scraper1-1"
    _stop "scraper1-2"
    _stop "scraper2-1"
    _stop "scraper2-2"
}

function restart-scraper() {
	stop-scraper
	start-scraper
}

function start-federator() {
    _start "federator1-1" 9011
    _start "federator1-2" 9012
}

function stop-federator() {
    _stop "federator1-1"
    _stop "federator1-2"
}

function restart-federator() {
	stop-federator
	start-federator
}

function start() {
	start-scraper
	start-federator
}

function stop() {
	stop-scraper
	stop-federator
}

function restart() {
    stop
    start
}

$COMMAND
