# MySQL: Playground

## Description

This is a playground for mysql using Docker Compose.

It uses the official mysql Docker image:  
https://hub.docker.com/_/mysql

## How to use

```
$ docker compose up -d
[+] Running 3/3
 ✔ Network playground_default      Created
 ✔ Volume playground_mysql-data  Created
 ✔ Container playground-mysql    Started

$ docker compose ps
NAME               IMAGE       COMMAND                  SERVICE   CREATED         STATUS                            PORTS
playground-mysql   mysql:9.5   "docker-entrypoint.s…"   mysql     3 seconds ago   Up 2 seconds (health: starting)   3306/tcp, 33060/tcp

17:49 [0] owner@dev01.pm.local.test:~/mylabo/labo/database/mysql/playground
$ docker compose ps
NAME               IMAGE       COMMAND                  SERVICE   CREATED          STATUS                    PORTS
playground-mysql   mysql:9.5   "docker-entrypoint.s…"   mysql     26 seconds ago   Up 25 seconds (healthy)   3306/tcp, 33060/tcp
```

```
$ docker exec -it playground-mysql mysql -h127.0.0.1 -usystem -psystempass pdns -e 'select * from records;'
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
 ✔ Container playground-mysql    Removed                                                                                                                 0.8s
 ✔ Volume playground_mysql-data  Removed                                                                                                                 0.0s
 ✔ Network playground_default    Removed                                                                                                                 0.2s
```
