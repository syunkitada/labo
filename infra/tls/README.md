# TLS

以下のコマンドにより、mylabo用の証明書を作成することができます。

```
$ make
```

上記のコマンド実行が完了すると以下のディレクトリに、CA用の証明書と、サーバ証明書が作成されます。

```
$ ls /etc/mylabo/tls-assets/
ca/  svc.local.test/
```

次に、CA用の証明書(ca.pem)を、サーバやブラウザなどで事前に信頼させておいてください。

makeを実行したサーバでは、この証明書を信頼する設定も自動で行われているこの作業は不要です。

サーバでの証明書を信頼する設定は方法は、[trust-ca-certs.sh](./scripts/trust-ca-certs.sh) を参考にしてください。

```
$ cat /etc/mylabo/tls-assets/ca/ca-certs/ca.pem
```

"svc.local.test" ディレクトリには、以下のファイルが生成されています。

```
$ ls /etc/mylabo/tls-assets/svc.local.test/
server-bundle.pem  server-csr.json  server-key.pem  server.csr  server.pem
```

server.pem, server-key.pem をWEBサーバに読み込ませることで、"\*.svc.local.test" でのTLS通信が利用できるようになります。

nginxでの利用例は、[labo/webserver/nginx/playground-tls](/labo/webserver/nginx/playground-tls/README.md) を参照してください。

server-bundle.pem は、server.pem, server-key.pem をバンドルしたもので、haproxyはこれを読み込ませることで、TLS通信が利用できるようになります。
