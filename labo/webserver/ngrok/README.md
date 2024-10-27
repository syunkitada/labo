# ngrok

- https://ngrok.com/
- All-in-one API gateway, Kubernetes Ingress, DDoS protection, firewall, and global load balancing as a service

## Use case1: Developer Preview

- https://ngrok.com/use-cases/developer-preview
- ローカルPC上のネットワークアプリケーションをインターネット上で公開できます。

### How to use

1. ngrok公式サイトからユーザ登録します。
2. ログイン後のGetting Startedを行います。
   1. ngrokコマンドをインストールします。
   2. ngrok config add-authtoken ...
3. 0.0.0.0:8080でListenするHTTPサーバを立ち上げます。
4. ngrok http http://localhost:8080 を実行して、インターネット上にHTTPサーバを公開できます。

```
$ ngrok http http://localhost:8080
...

Session Status                online
Account                       XXX (Plan: Free)
Version                       3.17.0
Region                        Japan (jp)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://XXX.ngrok-free.app -> http://localhost:8080

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00

```

インターネット上から、 https://XXX.ngrok-free.app にアクセスできるようになります。
