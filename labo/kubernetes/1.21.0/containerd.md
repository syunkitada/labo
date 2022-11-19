# containerd

## ctr

```
# image のダウンロード
$ sudo ctr images pull docker.io/library/nginx:latest

# containerの起動
$ sudo ctr run docker.io/library/nginx:latest nginx-test

# containerの一覧表示
$ sudo ctr c list
```
