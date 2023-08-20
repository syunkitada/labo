# memo

以下のコマンドでプロジェクトのひな型を生成します。

```
$ mkdir markdown-view
$ cd markdown-view
$ kubebuilder init --domain zoetrope.github.io --repo github.com/zoetrope/markdown-view
# --domain で指定した名前はCRDのグループ名に使われます。あなたの所属する組織が保持するドメインなどを利用して、ユニークでvalidな名前を指定してください。
# --repo にはgo modulesのmodule名を指定します。GitHubにリポジトリを作る場合は github.com/<user_name>/<product_name>を指定します。
```

```bash
.
├── Dockerfile
├── Makefile
├── PROJECT
├── README.md
├── cmd
│   └── main.go
        # main.go の中に、 //+kubebuilder:scaffold:imports, //+kubebuilder:scaffold:scheme, //+kubebuilder:scaffold:builder などのコメントが記述されています。
        # kubebuilerはこれらのコメントを目印にソースコードの自動生成を行うので、決して削除しないように注意してください。
├── config
    # configディレクトリ配下には、カスタムコントローラをKubernetesにデプロイするためのマニフェストが生成されます。
    # 実装する機能によっては必要のないマニフェストも含まれるので、適切に取捨選択してください。
│   ├── default
        # マニフェストをまとめて利用するための設定が記述されています。
        # 利用するマニフェストに応じて、kustomization.yamlを編集してください。
│   │   ├── kustomization.yaml
│   │   ├── manager_auth_proxy_patch.yaml
            # kube-auth-proxyを利用するために必要なパッチです。
            # kube-auth-proxyを利用しない場合は削除しても問題ありません。
│   │   └── manager_config_patch.yaml
            # カスタムコントローラのオプションを引数ではなくConfigMapで設定するためのパッチファイルです。
│   ├── manager
        # カスタムコントローラのDeploymentリソースのマニフェストです。
        # カスタムコントローラのコマンドラインオプションの変更をおこなった場合など、必要に応じて書き換えてください。
│   │   ├── kustomization.yaml
│   │   └── manager.yaml
│   ├── prometheus
        # Prometheus Operator用のカスタムリソースのマニフェストです。
        # Prometheus Operatorを利用している場合、このマニフェストを適用するとPrometheusが自動的にカスタムコントローラのメトリクスを収集してくれるようになります。
│   │   ├── kustomization.yaml
│   │   └── monitor.yaml
│   └── rbac
        # 各種権限を設定するためのマニフェストです。
│       ├── auth_proxy_client_clusterrole.yaml
│       ├── auth_proxy_role.yaml
│       ├── auth_proxy_role_binding.yaml
│       ├── auth_proxy_service.yaml
            # auth_proxy_から始まる4つのファイルは、kube-auth-proxy用のマニフェストです。
            # kube-auth-proxyを利用するとメトリクスエンドポイントへのアクセスをRBACで制限できます。
│       ├── kustomization.yaml
│       ├── leader_election_role.yaml
│       ├── leader_election_role_binding.yaml
            # leader_election_から始まる2つのファイルは、リーダーエレクション機能を利用するために必要な権限です。
│       ├── role_binding.yaml
│       └── service_account.yaml
            # role_binding.yaml, service_account.yamlは、コントローラが各種リソースにアクセスするための権限を設定するマニフェストです。
├── go.mod
├── go.sum
└── hack
    └── boilerplate.go.txt
      # boilerplate.go.txt は、自動生成されるソースコードの先頭に挿入されるボイラープレートです。
```

## API のひな型作成

以下のコマンドで、カスタムリソースとカスタムコントローラのひな型を生成します。

```
$ kubebuilder create api --group view --version v1 --kind MarkdownView --resource --controller
# --kind: 作成するリソースの名前を指定します。
# --group: リソースが属するごループ名を指定します。
# --version: 適切なバージョンを指定します。今後仕様が変わる可能性があるならv1alpha1, v1beta1を指定し、安定版であればv1を指定します。

$ make manifests
```

```
.
├── api
│   └── v1
│       ├── groupversion_info.go
            # これは初期生成後に編集する必要はありません。
│       ├── markdownview_types.go
            # MarkdownViewリソースをGo言語のstructで表現したものです。
            # 今後、MarkdownViewリソースの定義を変更するばあにはこのファイルを編集していくことになります。
│       └── zz_generated.deepcopy.go
            # これはmarkdownview_types.goの内容から自動生成されるファイルなので編集する必要はありません。
├── bin
│   └── controller-gen
├── cmd
│   └── main.go
        # create api実行後に、controllerの初期化処理が追加されています。
├── config
│   ├── crd
        # crdディレクトリにはCRD(Custom Resource Definition)のマニフェストが追加されています。
        # これらのマニフェストはmarkdownview_types.goから自動生成されるものなので、基本的に手動で編集する必要はありません。
        # ただし、Conversion Webhookを利用したい場合は、cainjection_in_markdownView.yamlとwebhook_in_markdownViews.yamlのパッチを利用するようにkustomization.yamlを書き換えてください。
│   │   ├── bases
│   │   │   └── view.zoetrope.github.io_markdownviews.yaml
│   │   ├── kustomization.yaml
│   │   ├── kustomizeconfig.yaml
│   │   └── patches
│   │       ├── cainjection_in_markdownviews.yaml
│   │       └── webhook_in_markdownviews.yaml
│   ├── rbac
        # role.yaml には、MarkdownViewリソースを扱うための権限が追加されています。
        # markdownview_editor_role.yaml と markdownview_viewer_role.yaml は、MarkdownViewリソースの編集・読み取りの権限です。必要に応じて利用しましょう。
│   │   ├── markdownview_editor_role.yaml
│   │   ├── markdownview_viewer_role.yaml
│   │   ├── role.yaml
│   └── samples
        # カスタムリソースのサンプルマニフェストです。テストで利用したり、ユーザ向けに提供できるように記述しておきましょう。
│       ├── kustomization.yaml
│       └── view_v1_markdownview.yaml
└── internal
    └── controller
        ├── markdownview_controller.go
        └── suite_test.go
```

## Webhook の生成

Kubernetes には、Admission Webhook と呼ばれる拡張機能があります。  
これは特定のリソースを作成・更新する際に Webhook API を呼び出し、バリデーションやリソースの書き換えを行うための機能です。

- --programmatic-validation: リソースのバリデーションを行うための Webhook
- --defaulting: リソースのフィールドにデフォルト値を設定するための Webhook
- --conversion: カスタムリソースのバージョンアップ時にリソースの変換を行うための Webhook

```
$ kubebuilder create webhook --group view --version v1 --kind MarkdownView --programmatic-validation --defaulting
$ make manifests
```

```
.
├── api
│   └── v1
│       ├── markdownview_webhook.go
            # Webhook実装のひな型です。
            # このファイルにWebhookの実装を追加していくことになります。
│       ├── webhook_suite_test.go
├── cmd
│   └── main.go
        # create webhook実行後に、webhookの初期化をおこなうためのコードが追加されています。
├── config
│   ├── certmanager
        # Admission Webhook機能を利用するためには証明書が必要となります。
        # cert-managerを利用して証明書を発行するためのカスタムリソースが生成されています。
│   │   ├── certificate.yaml
│   │   ├── kustomization.yaml
│   │   └── kustomizeconfig.yaml
│   ├── default
│   │   ├── manager_webhook_patch.yaml
│   │   └── webhookcainjection_patch.yaml
│   └── webhook
        # webhook機能を利用するために必要なマニフェストファイルです。
│       ├── kustomization.yaml
│       ├── kustomizeconfig.yaml
│       ├── manifests.yaml
            # manifests.yamlファイルは make manifestsで自動生成されるため、基本的に手動で編集する必要はありません。
│       └── service.yaml
```

kubebuilder コマンドで生成した直後の状態では、make manifests コマンドでマニフェストを生成しても、Webhook 機能が利用できるようにはなってません。
config/default/kustomization.yaml ファイルを編集する必要があります。

生成直後の kustomization.yaml は、resources の ../webhook と ../certmanager, patchesStrategicMerge の manager_webhook_patch.yaml と webhookcainjection_patch.yaml, replacements がコメントアウトされていますが、これらのコメントを外します。

```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -rf kubectl*
```

```
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
sudo kind create cluster
```

```
$ sudo kind get clusters
$ sudo kubectl cluster-info --context kind-kind
$ sudo kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/latest/download/cert-manager.yaml
```

```
$ sudo make docker-build
$ sudo kind load docker-image controller:latest

$ sudo make install
$ sudo make deploy
```

## controller-tools

- Kubebuilder では、カスタムコントローラの開発を補助するためのツール軍として controller-tools を提供しています。
- controller-tools には以下のツールが含まれています。
  - controller-gen
  - type-scaffold
  - helpgen

### controller-gen

- controller-gen は、Go のソースコードをもとにしてマニフェストや Go のソースコードの生成を行うツールです。

```
$ bin/controller-gen -h
...
generators

+webhook[:headerFile=<string>][,year=<string>]                                                                                                                                           package  generates (partial) {Mutating,Validating}WebhookConfiguration objects.
+schemapatch[:generateEmbeddedObjectMeta=<bool>],manifests=<string>[,maxDescLen=<int>]                                                                                                   package  patches existing CRDs with new schemata.
+rbac[:headerFile=<string>],roleName=<string>[,year=<string>]                                                                                                                            package  generates ClusterRole objects.
+object[:headerFile=<string>][,year=<string>]                                                                                                                                            package  generates code containing DeepCopy, DeepCopyInto, and DeepCopyObject method implementations.
+crd[:allowDangerousTypes=<bool>][,crdVersions=<[]string>][,generateEmbeddedObjectMeta=<bool>][,headerFile=<string>][,ignoreUnexportedFields=<bool>][,maxDescLen=<int>][,year=<string>]  package  generates CustomResourceDefinition objects.
```

- kubebuilder が生成した Makefile には、make manifests と make generate というターゲットが用意されており、make manifests では webhook, rbac, crd の生成、make generate では object の生成が行われます
- controller-gen がマニフェストの生成を行う際には、Go の struct の構成と、ソースコード中に埋め込まれた // +kubebuilder: から始まるコメント（マーカと呼ばれる）を目印にします。
- 利用可能なマーカーは下記のコマンドで確認できます。(-ww や-www を指定するとより詳細な説明が確認できます）

```
$ controller-gen crd -w
$ controller-gen webhook -w
```

#### CRD マニフェストの生成

- markdownview_types.go のフィールド定義で、CRD を定義し、Validation などの設定を行うことができます。
- 定義が完了したら make manifests でマニフェストを生成します。

```
 27 type MarkdownViewSpec struct {
 28     // Markdowns contain the markdown files you want to display.
 29     // The key indicates the file name and must not overlap with the keys.
 30     // The value is the content in markdown format.
 31     //+kubebuilder:validation:Required
 32     //+kubebuilder:validation:MinProperties=1
 33     Markdowns map[string]string `json:"markdowns,omitempty"`
 34
 35     // Replicas is the number of viewers.
 36     // +kubebuilder:default=1
 37     // +optional
 38     Replicas int32 `json:"replicas,omitempty"`
 39
 40     // ViewerImage is the image name of the viewer.
 41     // +optional
 42     ViewerImage string `json:"viewerImage,omitempty"`
 43 }
```

#### RBAC マニフェストの生成

- markdownview_controller.go の //+kubebuilder:rbac:xxx でコントローラに必要な権限を定義します。
- 定義が完了したら make manifests でマニフェストを生成します。

#### Webhook マニフェストの生成

- markdownview_webhook.go で Webhook の設定を行います。
- 定義が完了したら make manifests でマニフェストを生成します。

## controller-runtime

- カスタムコントローラを開発するためには、Kubernetes が標準で提供している client-go, apimachinery, api などのパッケージを利用することになります。
- 代表的なコンポーネント
  - manager.Manager
    - 複数のコントローラをまとめて管理するためのコンポーネントです。
    - リーダエレクションやメトリクスサーバ機能、カスタムコントローラを実装するための様々な機能をもっています。
  - client.Client
    - Kubernetes の kube-apiserver とやりとりするためのクライアントです。
    - 監視対象のリソースをインメモリにキャッシュする機能などを持ち、カスタムリソースも型安全に扱うことが可能なクライアントとなっています。
  - reconcile.Reconciler
    - カスタムコントローラが実装すべきインターフェイス
