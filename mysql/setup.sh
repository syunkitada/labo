#!/bin/bash -x

sudo docker ps | grep " mysql$" || \
    ( \
        ((sudo docker ps --all | grep " mysql$" && sudo docker rm mysql) || echo "mysql not found") && \
        sudo docker run -v "/var/lib/docker-mysql":/var/lib/mysql --net=host --name mysql -e MYSQL_ROOT_PASSWORD=rootpass -d mysql \
    )

NEXT_WAIT_TIME=0
until mysql -uroot -prootpass -h127.0.0.1 -e "show databases;" || [ $NEXT_WAIT_TIME -eq 4 ]; do
   sleep $(( NEXT_WAIT_TIME++ ))
done
mysql -uroot -prootpass -h127.0.0.1 -e "CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'adminpass';"
mysql -uroot -prootpass -h127.0.0.1 -e "GRANT ALL ON *.* TO 'admin'@'%'; FLUSH PRIVILEGES;"

cat << EOS | tee ~/.my.cnf
[client]
host=127.0.0.1
port=3306
user=admin
password=adminpass
EOS
