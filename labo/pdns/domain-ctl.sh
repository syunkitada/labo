#!/bin/bash

COMMAND="${*:-help}"

function help() {
	cat <<EOS
# show domains
$ labo-domain-ctl list

# create domain
$ labo-domain-ctl create example.com [ns]

# delete domain
$ labo-domain-ctl delete example.com
EOS
}

function list() {
	mysql-docker pdns -e "SELECT * FROM domains;"
}

function create() {
	if [ $# != 2 ]; then
		help "create [domain] [ns]"
		exit 1
	fi
	domain=$1
	ns=$2
	mysql-docker pdns -e "SELECT * FROM domains WHERE name = '$domain';" | grep "$domain" ||
		mysql-docker pdns -e "INSERT INTO domains (name, master, last_check, type, notified_serial, account) VALUES 
      ('$domain', NULL, NULL, 'NATIVE', NULL, NULL);"
	domain_id=$(mysql-docker pdns -e "SELECT id, name FROM domains WHERE name = '$domain';" | grep "$domain" | awk '{print $1}')
	mysql-docker pdns -e "SELECT * FROM records WHERE name = '$domain';" | grep "$domain" ||
		mysql-docker pdns -e "INSERT INTO \`records\` (domain_id,name,type,content,ttl,prio) VALUES
      ('$domain_id', '$domain', 'SOA', 'ns1.example.com admin.example.com $(date +%Y%m%d%H) 10800 1800 604800 86400', '3600', '0'),
      ('$domain_id', '$domain', 'NS', '$ns', '3600', '0');"

	echo "created"
}

function delete() {
	if [ $# != 1 ]; then
		help
		exit 1
	fi
	domain=$1
	domain_id=$(mysql-docker pdns -e "SELECT id, name FROM domains WHERE name = '$domain';" | grep "$domain" | awk '{print $1}')
	mysql-docker pdns -e "DELETE FROM records WHERE domain_id = '$domain_id';"
	mysql-docker pdns -e "DELETE FROM domains WHERE name = '$domain';"
	echo "deleted $domain"
}

$COMMAND
