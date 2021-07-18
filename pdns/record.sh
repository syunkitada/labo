#!/bin/bash

COMMAND="${@:-help}"

function help() {
    cat << EOS
# show records
./record.sh list

# create A record
./record.sh create example.com hoge.example.com 192.168.1.1

# delete record
./record.sh delete hoge.example.com
EOS
}

function list() {
    mysql pdns -e "SELECT * FROM records;"
}

function create() {
    if [ $# != 3 ]; then
        help
        exit 1
    fi
    domain=$1
    record=$2
    ip=$3
    domain_id=`mysql pdns -e "SELECT id, name FROM domains WHERE name = '$domain';" | grep $domain | awk '{print $1}'`

    mysql pdns -e "SELECT * FROM records WHERE name = '$record';" | grep $record || \
      mysql pdns -e "INSERT INTO \`records\` (domain_id,name,type,content,ttl,prio) VALUES
      ('$domain_id', '$record', 'A', '$ip', '3600', '0');"
    echo "created"
}

function delete() {
    if [ $# != 1 ]; then
        help
        exit 1
    fi
    record=$1
    mysql pdns -e "DELETE FROM records WHERE name = '$record';"
    echo "deleted $record"
}

$COMMAND
