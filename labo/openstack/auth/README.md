# auth

## keystonemiddleware.auth_token

- ドキュメント
  - https://docs.openstack.org/keystonemiddleware/latest/middlewarearchitecture.html
- ソースコード
  - https://github.com/openstack/keystonemiddleware/blob/master/keystonemiddleware/auth_token/__init__.py

auth_tokenは、nova-apiやglance-apiなどのAPIで利用されている認証用のミドルウェアです。

1. auth_tokenは、TOKENを検証しその認証情報をHTTP Headerにセットします
   - どのようなヘッダ情報がセットされるかは、[ソースコード](https://github.com/openstack/keystonemiddleware/blob/master/keystonemiddleware/auth_token/__init__.py)を見るとよい
     - ユーザ名・ID、プロジェクト名・ID、カタログリストなど
   - auth_tokenは、TOKENの検証時にすでにそのTOKENが検証済みかどうかキャッシュから調べます
   - キャッシュにTOKENがない場合は、KeystoneによってTOKENを検証して認証情報を得ます
     - この検証結果は次回の検証用にキャッシュに保存します
   - キャッシュにTOKENがある場合は、Keystoneへはアクセスせずに前回の検証結果の認証情報を利用します
2. 後続のミドルウェアは、HTTP Hedaerの認証情報を利用してrequest contextを生成し、リクエストを処理する
