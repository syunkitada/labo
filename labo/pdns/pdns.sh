#!/bin/bash -x

# settings
# https://doc.powerdns.com/authoritative/settings.html

test -e /tmp/.laboenvrc && source /tmp/.laboenvrc

mysql-docker -e 'CREATE DATABASE IF NOT EXISTS pdns'

PDNS_LOCAL_ADDRESS=${PDNS_LOCAL_ADDRESS:-127.0.0.1}
PDNS_DOMAIN=${PDNS_DOMAIN:-example.com}
MYSQL_ADMIN_USER=${MYSQL_ADMIN_USER:-admin}
MYSQL_ADMIN_PASSWORD=${MYSQL_ADMIN_PASSWORD:-adminpass}

sudo docker ps | grep pdns-mysql && sudo docker kill pdns-mysql || echo "pdns-mysql not found"
sudo docker ps | grep pdns-mysql ||
	( 
		(sudo docker ps --all | grep pdns && sudo docker rm pdns-mysql || echo "pdns-mysql not found") &&
			sudo docker run --rm -d --network host --name pdns-mysql \
				-e PDNS_local_address=127.0.0.1 \
				-e PDNS_local_port=8053 \
				-e PDNS_master=yes \
				-e PDNS_default_ttl=1500 \
				-e PDNS_gmysql_host=127.0.0.1 \
				-e PDNS_gmysql_port=3306 \
				-e PDNS_gmysql_user="${MYSQL_ADMIN_USER}" \
				-e PDNS_gmysql_password="${MYSQL_ADMIN_PASSWORD}" \
				-e PDNS_gmysql_dbname=pdns \
				pschiffe/pdns-mysql
	)

sudo docker ps | grep pdns-recursor && sudo docker kill pdns-recursor || echo "pdns-recursor not found"
sudo docker ps | grep pdns-recursor ||
	( 
		(sudo docker ps --all | grep pdns-recursor && sudo docker rm pdns-recursor || echo "pdns-recursor not found") &&
			sudo docker run --rm -d --network host --name pdns-recursor \
				-e PDNS_local_address="${PDNS_LOCAL_ADDRESS}" \
				-e PDNS_local_port=53 \
				-e PDNS_forward_zones_recurse=.=8.8.8.8 \
				-e PDNS_forward_zones="${PDNS_DOMAIN}"=127.0.0.1:8053 \
				pschiffe/pdns-recursor
	)

# MEMO 0.0.0.0でリッスンする場合は、ubuntuだとsystemd-resolvedがスタブとして起動してるとバッティングするので止めておく必要がある
# sudo systemctl stop systemd-resolved
