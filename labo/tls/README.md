# TLS

以下のコマンドにより、Labo用の証明書を作成することができます。

このコマンドは、Laboの初期セットアップ時のmake内部でも呼び出されています。

```
$ make
```

上記のコマンド実行が完了すると以下のディレクトリに、CA用の証明書と、サーバ証明書が作成されます。

```
$ ls /etc/labo/tls-assets/
ca/  localhost.test/
```

次に、CA用の証明書(ca.pem)を、サーバやブラウザなどで事前に信頼させておいてください。

makeを実行したサーバでは、この証明書を信頼する設定も自動で行われているこの作業は不要です。

サーバでの証明書を信頼する設定は方法は、[trust-ca-certs.sh](./scripts/trust-ca-certs.sh) を参考にしてください。

```
$ cat /etc/labo/tls-assets/ca/ca-certs/ca.pem
```

"localhost.test" ディレクトリには、以下のファイルが生成されています。

```
$ ls /etc/labo/tls-assets/localhost.test/
server-csr.json  server-key.pem  server.csr  server.pem
```

server-key.pem, server.pem をWEBサーバに読み込ませることで、"\*.localhost.test" でのTLS通信が利用できるようになります。

例: [nginxで利用する例](../webserver/nginx/plgyground-tls/)
