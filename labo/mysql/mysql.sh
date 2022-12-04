#!/bin/bash

set -x

test -e /tmp/.laboenvrc && source /tmp/.laboenvrc

MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-rootpass}
MYSQL_ADMIN_USER=${MYSQL_ADMIN_USER:-admin}
MYSQL_ADMIN_PASSWORD=${MYSQL_ADMIN_PASSWORD:-adminpass}

sudo docker ps | grep " mysql$" ||
	( 
		(sudo docker ps --all | grep " mysql$" && sudo docker rm mysql || echo "mysql not found") &&
			sudo docker run -v "/var/lib/docker-mysql":/var/lib/mysql --net=host --name mysql -e MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" -d mysql
	)

cat <<EOS | sudo tee /usr/bin/mysql-docker
#!/bin/bash -e
sudo docker exec mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} "\$@"
EOS
sudo chmod 755 /usr/bin/mysql-docker

NEXT_WAIT_TIME=0
until mysql-docker -e "show databases;" || [ $NEXT_WAIT_TIME -eq 4 ]; do
	sleep $((NEXT_WAIT_TIME++))
done
mysql-docker -e "CREATE USER IF NOT EXISTS '${MYSQL_ADMIN_USER}'@'%' IDENTIFIED BY '${MYSQL_ADMIN_PASSWORD}';"
mysql-docker -e "GRANT ALL ON *.* TO '${MYSQL_ADMIN_USER}'@'%'; FLUSH PRIVILEGES;"

cat <<EOS | tee ~/.my.cnf
[client]
host=127.0.0.1
port=3306
user=${MYSQL_ADMIN_USER}
password=${MYSQL_ADMIN_PASSWORD}
EOS
