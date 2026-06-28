# DNS

## Description

```
DNS Client -> DNSDist ---(external domain) --> PDNS Recursor --> External DNS Server (e.g., Google DNS)
                       --(internal domain) --> PDNS Authoritative Server -> Database (MySQL)
                                                     ^
                                                     |
                                               PDNS Admin
```

Docker Images:

- https://hub.docker.com/r/powerdns/

## How to use

```
$ docker compose up -d

# Stop and remove containers, networks, volumes, and images created by `up`:
# $ docker compose down -v
```

Verify the setup by querying both internal and external domains:

```
$ dig +short dns01.sample.test
10.53.53.3
```

```
$ dig +short @127.0.0.1 -p1253 dns01.sample.test
10.53.53.3

$ dig +short @127.0.0.1 -p1253 google.com
142.251.42.206
```

# Debug container status

```
$ docker inspect mylabo-pdns-mysql --format '{{json .State.Health}}' | jq
{
  "Status": "starting",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2026-06-27T15:57:50.697028051+09:00",
      "End": "2026-06-27T15:57:50.771611962+09:00",
      "ExitCode": 1,
      "Output": "Enter password: ERROR 1045 (28000): Access denied for user 'system'@'127.0.0.1' (using password: NO)\n"
    },
    ...
  ]
}
```

# Debug MySQL

```
$ docker exec -it mylabo-pdns-mysql mysql -usystem -psystempass pdns
mysql> show tables;
+----------------+
| Tables_in_pdns |
+----------------+
| comments       |
| cryptokeys     |
| domainmetadata |
| domains        |
| records        |
| supermasters   |
| tsigkeys       |
+----------------+
7 rows in set (0.002 sec)
```

# Debug authoritative server

```
$ dig +short dns01.sample.test @127.0.0.1 -p1053
10.53.53.3
```

# Debug recursor server

```
$ dig +short google.com @127.0.0.1 -p1153
142.250.194.206
```

## DNSDist

- Access DNSDist web UI:
  - http://xxx:1280/
- Username: any
- Password: See `.env` file for `DNSDIST_API_KEY`

## PDNS Admin

1. Create an account on PDNS Admin:

- Access below URL:
  - http://xxx:9191/admin/setting/pdns
- Create an account

2. Login and Input Server Settings:

- PowerDNS API URL: http://mylabo-pdns-auth:8081/
- PowerDNS API Key: See `.env` file for `PDNS_AUTH_API_KEY`
