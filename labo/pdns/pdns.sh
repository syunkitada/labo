#!/bin/bash -x

# settings
# https://doc.powerdns.com/authoritative/settings.html


mysql -e "CREATE DATABASE IF NOT EXISTS pdns;"

sudo docker ps | grep pdns-mysql && sudo docker kill pdns-mysql || echo "pdns-mysql not found"
sudo docker ps | grep pdns-mysql || \
    ( \
        ((sudo docker ps --all | grep pdns && sudo docker rm pdns-mysql) || echo "pdns-mysql not found") && \
        sudo docker run -d --network host --name pdns-mysql \
            -e PDNS_local_address=127.0.0.1 \
            -e PDNS_local_port=8053 \
            -e PDNS_master=yes \
            -e PDNS_default_ttl=1500 \
            -e PDNS_gmysql_host=127.0.0.1 \
            -e PDNS_gmysql_port=3306 \
            -e PDNS_gmysql_user=admin \
            -e PDNS_gmysql_password=adminpass \
            -e PDNS_gmysql_dbname=pdns \
            pschiffe/pdns-mysql \
    )

sudo docker ps | grep pdns-recursor && sudo docker kill pdns-recursor || echo "pdns-recursor not found"
sudo docker ps | grep pdns-recursor || \
    ( \
        ((sudo docker ps --all | grep pdns-recursor && sudo docker rm pdns-recursor) || echo "pdns-recursor not found") && \
        sudo docker run -d --network host --name pdns-recursor \
            -e PDNS_forward_zones_recurse=.=8.8.8.8 \
            -e PDNS_forward_zones=example.com=127.0.0.1:8053 \
            pschiffe/pdns-recursor \
    )

# systemd-resolvedがスタブとして起動してるとバッティングするので止めておく
sudo systemctl stop systemd-resolved
