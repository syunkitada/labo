# MariaDB: Playground

## Description

This is a playground for [MariaDB](https://mariadb.org/) using Docker Compose.

It uses the official MariaDB Docker image:  
https://hub.docker.com/_/mariadb

## How to use

```
$ docker compose up -d
[+] Running 3/3
 ✔ Network playground_default      Created
 ✔ Volume playground_mariadb-data  Created
 ✔ Container playground-mariadb    Started

$ docker compose ps
NAME                 IMAGE          COMMAND                  SERVICE   CREATED          STATUS                             PORTS
playground-mariadb   mariadb:11.4   "docker-entrypoint.s…"   mariadb   20 seconds ago   Up 20 seconds (health: starting)   3306/tcp

$ docker compose ps
NAME                 IMAGE          COMMAND                  SERVICE   CREATED          STATUS                             PORTS
playground-mariadb   mariadb:11.4   "docker-entrypoint.s…"   mariadb   29 seconds ago   Up 29 seconds (health: starting)   3306/tcp
```

```
$ docker exec -it playground-mariadb mariadb -h127.0.0.1 -usystem -psystempass pdns -e 'select * from records;'
+----+-----------+------------+------+-------------------------------------------------------+------+------+----------+-----------+------+
| id | domain_id | name       | type | content                                               | ttl  | prio | disabled | ordername | auth |
+----+-----------+------------+------+-------------------------------------------------------+------+------+----------+-----------+------+
|  1 |         1 | home       | SOA  | dns01.home. hostmaster.home. 0 28800 3600 2419200 900 | 3600 |    0 |        0 | NULL      |    1 |
|  2 |         1 | home       | NS   | dns01.home.                                           | 3600 |    0 |        0 | NULL      |    1 |
|  3 |         1 | dns01.home | A    | 192.0.2.50                                            | 3600 |    0 |        0 | NULL      |    1 |
+----+-----------+------------+------+-------------------------------------------------------+------+------+----------+-----------+------+
```

## Cleanup

```
$ docker compose down -v
[+] Running 3/3
 ✔ Container playground-mariadb    Removed
 ✔ Volume playground_mariadb-data  Removed
 ✔ Network playground_default      Removed
```
