# TLS

```
# make TLS certs for LABO
$ make
```

以下に、CA用の証明書と、サーバ証明書が作成されます。

```
$ ls /etc/labo/tls-assets/
ca/  localhost.test/
```

ca.pemを、サーバやブラウザなどで事前に信頼させることが必要です。
makeを実行したサーバではこの設定が自動で行われます。

```
/etc/labo/tls-assets/ca/ca-certs/ca.pem
```

"localhost.test" には、以下のファイルが生成されており、server-key.pem, server.pemをWEBサーバに読み込ませることで、"\*.localhost.test"でのTLS通信が利用できるようになります。

例: [nginxで利用する例](../webserver/nginx/plgyground-tls/)

```
$ ls /etc/labo/tls-assets/localhost.test/
server-csr.json  server-key.pem  server.csr  server.pem
```
