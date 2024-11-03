# oauth2-proxy: playground

## How to use for GitHub

### Settings on GitHub

事前に、以下のURLからOAuth アプリケーションを作成してください。

https://github.com/settings/applications/new

入力項目:

- Application name: myapp
- Homepage URL: https://myapp.localhost.test
- Authorization callback URL: https://myapp.localhost.test

アプリケーションが作成で来たら、client_id、client_secret をメモしておきます。

### Settings on server host

次に、oauth2-proxyの設定ファイルを作成します。

```
$ cp oauth2_proxy/oauth2_proxy.cfg.tpl oauth2_proxy/oauth2_proxy.cfg
```

コメントアウトに従って必要な項目を埋めてください。

```
$ vim oauth2_proxy/oauth2_proxy.cfg
```

### Start playground

```
# Create playground
$ make

# Clean playground, when you no longer need it
$ make clean
```

### Access to your web site

myapp.localhost.test にアクセスできるよう、/etc/hosts にエントリを記載しておきます。

```
[your server ip]   myapp.localhost.test
```

ブラウザから、以下のアドレスにアクセスして、GitHubの認証を通してWebページにアクセスできることを確認してください。

https://myapp.localhost.test
