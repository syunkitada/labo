# PDNS: Playground

## Description

This is a playground for pdns using Docker Compose.

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
```

Verify the setup by querying both internal and external domains:

```
$ dig dns01.sample.test @127.0.0.1 -p5353 +time=2 +tries=1 +short
10.53.53.3

$ dig google.com @127.0.0.1 -p5353 +time=2 +tries=1 +short
142.251.42.206
```

# Debug authoritative server

```
$ dig +short dns01.sample.test @127.0.0.1 -p1053
10.53.53.3
```

# Debug recursor server

```
$ dig +short google.com @127.0.0.1 -p2053
142.250.194.206
```

## DNSDist

- Access DNSDist web UI:
  - http://xxx:1083/
- Username: any
- Password: See `.env` file for `DNSDIST_API_KEY`

## PDNS Admin

1. Create an account on PDNS Admin:

- Access below URL:
  - http://xxx:9191/admin/setting/pdns
- Create an account

2. Login and Input Server Settings:

- PowerDNS API URL: http://pdns-auth:8081/
- PowerDNS API Key: See `.env` file for `PDNS_AUTH_API_KEY`
