# NFS

## サーバ側

```
$ ./setup.sh
```

### 動作確認

```
$ rpcinfo -p
   program vers proto   port  service
    100000    4   tcp    111  portmapper
    100000    3   tcp    111  portmapper
    100000    2   tcp    111  portmapper
    100000    4   udp    111  portmapper
    100000    3   udp    111  portmapper
    100000    2   udp    111  portmapper
    100005    1   udp  38921  mountd
    100005    1   tcp  55951  mountd
    100005    2   udp  46891  mountd
    100005    2   tcp  56117  mountd
    100005    3   udp  37611  mountd
    100005    3   tcp  55409  mountd
    100003    3   tcp   2049  nfs
    100003    4   tcp   2049  nfs
    100227    3   tcp   2049
    100003    3   udp   2049  nfs
    100227    3   udp   2049
    100021    1   udp  42474  nlockmgr
    100021    3   udp  42474  nlockmgr
    100021    4   udp  42474  nlockmgr
    100021    1   tcp  38977  nlockmgr
    100021    3   tcp  38977  nlockmgr
    100021    4   tcp  38977  nlockmgr
```

## クライアント側(centos7)

```
$ sudo yum install -y nfs-utils

$ sudo mount -t nfs [server ip]:/ /mnt/nfs
```

## クライアント側(ubuntu20)

```
$ sudo apt install -y nfs-common

$ sudo mkdir -p /mnt/nfs
$ sudo mount -t nfs [server ip]:/ /mnt/nfs
```
