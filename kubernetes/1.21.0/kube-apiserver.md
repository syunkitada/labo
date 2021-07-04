# kube-apiserver

## 認証・認可・入力制御

- authentication, authorization, adminssion controll はそれぞれモジュール管理されており標準で複数提供されている
  - モジュールは API 起動時のオプションにより有効にできる
- API へのリクエスト処理の流れ
  - authentication(認証)
    - モジュール一覧
      - X509 Client Certs
        - --client-ca-file=[CA ファイル] を指定することで有効になる
        - クライアント証明書が提示され検証された場合、サブジェクトの CN(Common Name)がリクエストのユーザ名として使用される
        - Organaization フィールドを使用して、ユーザのグループメンバーシップを示すこともできる
      - Static Token File
        - --token-auth-file=[トークンファイル] を指定することで有効になる
        - API サーバはファイルから Bearer トークンを読み込む
        - トークンファイルは、トークン、ユーザー名、ユーザー UID の少なくとも 3 つの列を持つ csv ファイルで、その後にオプションでグループ名が付く
      - Bootstrap Tokens
        - --enable-bootstrap-token-auth を指定することで有効になる
        - クラスタ構築時に効率的にブートストラップを可能にするために、Bootstrap Token とよばれる動的に管理された Bearer トークンたプを利用できる
        - これは、まだ認証設定が行われていない状態で使うことを想定している
      - OpenID Connect Tokens
        - --oidc-\* を指定することで有効になる
        - OpenID Connect は、Azure Active Directory、Salesforce、Google など、いくつかの OAuth2 プロバイダーでサポートされている OAuth2 の一種
      - Webhook Token Authentication Webhook
        - --authentication-token-webhook-config-file=[設定ファイル] を指定することで有効になる
      - Authenticating Proxy
        - --requestheader-username-headers=[使用するヘッダ名] を指定することで有効になる
        - Authenticating Proxy 認証機能を持つプロキシなどが、「X-Remote-User」や「X-Remote-Group」といった HTTP ヘッダを使って認証情報を付与する
  - authorization(認可)
    - モジュール一覧
    - ABAC
      - 許可 policy を書いたファイルをあら化 j 目用意してファイルに従い認可する
    - RBAC
      - policy をリソース(Role, ClusterRole)として定義しておき、これに従って認可する
  - adminssion controll(入力制御)
    - リクエスト内容の内容をチェックして、リクエストをブロックしたり、リクエスト内容の修正を行う
    - --enable-admission-plugins=... で指定したプラグイン(モジュール)を有効にできる
    - モジュール一覧
      - NamespaceLifecycle
      - NodeRestriction
      - LimitRanger
      - ServiceAccount
      - DefaultStorageClass
      - ResourceQuota
- 参考
  - https://kubernetes.io/ja/docs/reference/access-authn-authz/authentication/
  - https://kubernetes.io/docs/reference/access-authn-authz/authentication/

## リスナポート

- 6443: 外部からの接続を受けるためのセキュアポート
- 8080: ローカルからの接続を受けるための非セキュアポート

## ユーザアカウントとサービスアカウント

- ユーザアカウント
  - 一般ユーザが利用するためのアカウント
  - ユーザ側(管理者)によって管理されるもの
  - クラスターの認証局(CA)に署名された有効な証明書のユーザーは認証済みと判断される
  - ユーザ名は証明書の CN から特定される
- サービスアカウント
  - サービス（Pod など）が認証するためのアカウント
  - Kubernetes によって管理されるもの
  - サービスアカウントは Namespace にバインドされる
  - 自動で作成される場合もあるし、明示的に作成する
  - サービスアカウントには Secret(Token)が紐づけられる
  - Secret は Pod にマウントされ、Kubernetes API と通信が可能になる
  - Pod の作成時に ServiceAccount が指定されていればそれを利用し、そうでなければ default が紐づく
