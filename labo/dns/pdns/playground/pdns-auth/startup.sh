#!/bin/bash -e

cd /pdns-auth

cat /etc/powerdns/pdns.conf

ls -al /etc/powerdns/

cp pdns.d/* /etc/powerdns/pdns.d/

sed -i "s/@PDNS_AUTH_API_KEY/${PDNS_AUTH_API_KEY}/g" /etc/powerdns/pdns.d/pdns.conf
sed -i "s/@MYSQL_SYSTEM_PASSWORD/${MYSQL_SYSTEM_PASSWORD}/g" /etc/powerdns/pdns.d/pdns.conf

/usr/local/sbin/pdns_server-startup
