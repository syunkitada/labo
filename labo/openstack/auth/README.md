# auth

## keystonemiddleware.auth_token

- ドキュメント
  - https://docs.openstack.org/keystonemiddleware/latest/middlewarearchitecture.html
- ソースコード
  - https://github.com/openstack/keystonemiddleware/blob/master/keystonemiddleware/auth_token/__init__.py

auth_tokenは、nova-apiやglance-apiなどのAPIで利用されている認証用のミドルウェアです。

1. auth_tokenは、TOKENを認証しその認証情報をHTTP Headerにセットします
   - どのようなヘッダ情報がセットされるかは、[ソースコード](https://github.com/openstack/keystonemiddleware/blob/master/keystonemiddleware/auth_token/__init__.py)を見るとよい
2. 後続のミドルウェアは、HTTP Hedaerの認証情報を利用してrequest contextを生成し、リクエストを処理する
