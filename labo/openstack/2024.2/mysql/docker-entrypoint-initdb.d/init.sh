#!/bin/bash -xe

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -e "
CREATE USER 'admin'@'%' IDENTIFIED BY 'adminpass';

GRANT ALL ON *.* TO 'admin'@'%';

FLUSH PRIVILEGES;
"
