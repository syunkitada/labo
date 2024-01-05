#!/bin/bash

COMMAND="${*:-help}"

function help() {
	cat <<EOS
# show records
./record.sh list [domain]
./record.sh list example.com

# create A record
./record.sh create [domain] [record] [type] [content]
./record.sh create example.com hoge.example.com a 192.168.1.1

# delete record
./record.sh delete hoge.example.com
EOS
}

function list() {
	if [ $# != 1 ]; then
		help
		exit 1
	fi
	domain_name=$1
	domain_id=$(mysql-docker pdns -e "SELECT id, name FROM domains WHERE name = '$domain_name';" | grep "$domain_name" | awk '{print $1}')
	mysql-docker pdns -e "SELECT name,type,content,ttl FROM records WHERE domain_id = ${domain_id}"
}

function create() {
	if [ $# != 4 ]; then
		help
		exit 1
	fi
	domain=$1
	record=$2
	record_type=$3
	record_content=$4
	domain_id=$(mysql-docker pdns -e "SELECT id, name FROM domains WHERE name = '$domain';" | grep "$domain" | awk '{print $1}')

	mysql-docker pdns -e "SELECT * FROM records WHERE name = '$record';" | grep "$record" ||
		mysql-docker pdns -e "INSERT INTO \`records\` (domain_id,name,type,content,ttl,prio) VALUES
      ('$domain_id', '$record', '${record_type}', '${record_content}', '3600', '0');"
	echo "created"
}

function delete() {
	if [ $# != 1 ]; then
		help
		exit 1
	fi
	record=$1
	mysql-docker pdns -e "DELETE FROM records WHERE name = '$record';"
	echo "deleted $record"
}

$COMMAND
