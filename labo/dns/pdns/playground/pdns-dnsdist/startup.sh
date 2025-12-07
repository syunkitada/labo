#!/bin/bash -ex

cd /pdns-dnsdist

ls -sl /etc/dnsdist/

cp /pdns-dnsdist/dnsdist.yml /etc/dnsdist/conf.d
sed -i "s/@DNSDIST_API_KEY/${DNSDIST_API_KEY}/g" /etc/dnsdist/conf.d/dnsdist.yml

/usr/local/bin/dnsdist-startup -C /etc/dnsdist/conf.d/dnsdist.yml
