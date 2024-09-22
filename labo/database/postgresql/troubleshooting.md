## Troubleshooting

### kind上でPostgreSQLが動かない

エラーの内容

```
$ sudo kubectl logs -n postgres postgres-6766d5c987-44wfs
The files belonging to this database system will be owned by user "postgres".
This user must also own the server process.

The database cluster will be initialized with locale "en_US.utf8".
The default database encoding has accordingly been set to "UTF8".
The default text search configuration will be set to "english".

Data page checksums are disabled.

fixing permissions on existing directory /var/lib/postgresql/data ... ok
creating subdirectories ... ok
selecting dynamic shared memory implementation ... posix
selecting default max_connections ... 20
selecting default shared_buffers ... 400kB
selecting default time zone ... Etc/UTC
creating configuration files ... ok
Bus error (core dumped)
child process exited with exit code 135
initdb: removing contents of data directory "/var/lib/postgresql/data"
```

manifest

```
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: postgres
  name: postgres
spec:
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: docker.io/library/postgres
          env:
            - name: POSTGRES_PASSWORD
              value: postgres
```

Docker上ではpostgresが動くことが確認できた。

また、Docker on Docker上でもpostgresが動くことが確認できた。

```
$ docker run --rm --name postgres-test -e POSTGRES_PASSWORD=postgres docker.io/library/postgres
```

hugepageが有効になっている場合は、勝手に利用される。

```
$ cat /proc/meminfo
HugePages_Total:       2
HugePages_Free:        1
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:    1048576 kB

$ sudo grep "KernelPageSize:.*1048576*" /proc/[[:digit:]]*/smaps | awk {'print $1'} | cut -d "/" -f3 | sort | uniq
1722326
1722407
1722408
1722410
1722411
1722412

$ ps ax | grep 1722326
1722326 ?        Ss     0:00 postgres
```

kindのworker上で直接以下を実行できることも確認できた。(k8sを通すとダメそう)

```
$ ctr image pull docker.io/library/postgres:13
$ ctr run --rm --env POSTGRES_PASSWORD=postgres docker.io/library/postgres:13 postgres-test
```

以下によると、hugepageが利用できないにもかかわらず、k8s上で稼働しようとするとhugepageを利用しようとしてしまいエラーとなる。

- https://www.enterprisedb.com/docs/postgres_for_kubernetes/latest/troubleshooting/#error-while-bootstrapping-the-data-directory
- https://github.com/docker-library/postgres/issues/451#issuecomment-447472044

これは、HOST上のhugepagesを無効化することで回避できた。

```
$ sudo sh -c 'echo "0" > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages'

$ cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
0
```

また、postgresのhugepageの利用を無効化するか、k8sでhugepageを利用できるようにすることで回避ができる。
