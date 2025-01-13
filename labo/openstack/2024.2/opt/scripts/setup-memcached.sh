#!/bin/bash -xe

yum install -y memcached

systemctl start memcached
