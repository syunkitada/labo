import os
import time


def make(c, spec, rspec):
    rootpass = "rootpass"
    if rspec["name"] not in c.docker_ps_map:
        c.sudo(
            f"docker run --rm -d -v '/var/lib/docker-mysql':/var/lib/mysql --net=host --name {rspec['name']} -e MYSQL_ROOT_PASSWORD={rootpass} mysql"
        )

    for _ in range(4):
        if c.sudo("mysql -uroot -prootpass -h127.0.0.1 -e 'show databases'", warn=True).ok:
            break
        time.sleep(1)
    else:
        raise Exception("")

    c.run("mysql -uroot -prootpass -h127.0.0.1 -e \"CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'adminpass';\"")
    c.run("mysql -uroot -prootpass -h127.0.0.1 -e \"GRANT ALL ON *.* TO 'admin'@'%'; FLUSH PRIVILEGES;\"")
    with open(os.path.join(os.environ["HOME"], ".my.cnf"), "w") as f:
        f.write(
            """
[client]
host=127.0.0.1
port=3306
user=admin
password=adminpass
"""
        )
    return
