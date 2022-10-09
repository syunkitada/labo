# kubebuilder

- 「[つくって学ぶ Kubebuilder](https://zoetrope.github.io/kubebuilder-training/)」をやってみてのメモ書き
- 上記との差分
  - Kind は使わずに手動構築した kubernetes で kubebuilder を使う
  - 初期化時
    - mkdir -p $PJ_DIR/kubebuilder-traging/markdown-view
    - cd $PJ_DIR/kubebuilder-traging/markdown-view
    - kubebuilder init --domain kubebuilder.example.com --repo github.com/syunkitada/kubebuilder-traging-markdown-view

```
$ curl -L -o kubebuilder https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)
$ chmod +x kubebuilder && sudo mv kubebuilder /usr/local/bin/
```

- k8s では、あるリソースの状態をチェックして何らかの処理を行うプログラムをコントローラと呼びます。
  - https://github.com/kubernetes/kubernetes/tree/master/pkg/controller
  - deployment を管理するコントローラは、kube-apiserver に Deployment リソースが登録されると対応する ReplicaSet リソースを新たに作成します。
  - 次に ReplicaSet を管理するコントローラは、ReplicaSet リソースが登録されると spec.replicas に指定された 3 つの Pod を新たに作成します。
  - kube-scheduler は、kube-apiserver に Pod リソースが登録されると、Pod を配置するノードを決定し Pod の情報を更新します。
  - kubelet は、自分のノード名が記述された Pod リソースを見つけるとコンテナを立ち上げます。
- ユーザが定義したコントローラをカスタムコントローラと呼ぶ
- Imperative(命令型)と Declarative(宣言的)
  - k8s は Declarative
- Reconcilation Loop
  - リソースに記述された状態を理想都市、システムの現在の状態と比較し、その差分がなくなるように調整する処理を無限ループで実行し続けます。
    - エッジドリブントリガーとレベルドリブントリガー
      - エッジドリブントリガー: 状態が変化したイベントに応じて処理を実行すること
        - イベントをロストした場合に、あるべき状態と現在の状態がずれてしまう
      - レベルドリブントリガー: 現在の状態に応じて処理を実行すること
        - イベントをロストしても現在の状態を見て、あるべき状態に収束することが可能
    - k8s ではレベルドリブントリガーを採用しており、変化が生じた際に Reconcilation Loop によってあるべき状態へ収束させる

## メモ

- docker build は、sudo が必要だったので、meke docker-build を実行した後に、sudo docker-build を実行する必要があった

```
$ make docker-build
/home/owner/kubernetes_1.25.1/kubebuilder-traging/markdown-view/bin/controller-gen rbac:roleName=manager-role crd webhook paths="./..." output:crd:artifacts:config=config/crd/bases
/home/owner/kubernetes_1.25.1/kubebuilder-traging/markdown-view/bin/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./..."
go fmt ./...
go vet ./...
test -s /home/owner/kubernetes_1.25.1/kubebuilder-traging/markdown-view/bin/setup-envtest || GOBIN=/home/owner/kubernetes_1.25.1/kubebuilder-traging/markdown-view/bin go install sigs.k8s.io/controller-runtime/tools/setup-envtest@latest
go: downloading sigs.k8s.io/controller-runtime/tools/setup-envtest v0.0.0-20220907012636-c83076e9f792
go: downloading github.com/spf13/afero v1.6.0
go: downloading github.com/go-logr/zapr v1.2.0
go: downloading go.uber.org/zap v1.19.1
KUBEBUILDER_ASSETS="/home/owner/kubernetes_1.25.1/kubebuilder-traging/markdown-view/bin/k8s/1.25.0-linux-amd64" go test ./... -coverprofile cover.out
?       github.com/syunkitada/kubebuilder-traging-markdown-view [no test files]
ok      github.com/syunkitada/kubebuilder-traging-markdown-view/api/v1  0.026s  coverage: 2.0% of statements
ok      github.com/syunkitada/kubebuilder-traging-markdown-view/controllers     0.026s  coverage: 0.0% of statements
docker build -t controller:latest .
WARNING: Error loading config file: /home/owner/.docker/config.json: open /home/owner/.docker/config.json: permission denied
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/build?buildargs=%7B%7D&cachefrom=%5B%5D&cgroupparent=&cpuperiod=0&cpuquota=0&cpusetcpus=&cpusetmems=&cpushares=0&dockerfile=Dockerfile&labels=%7B%7D&memory=0&memswap=0&networkmode=default&rm=1&shmsize=0&t=controller%3Alatest&target=&ulimits=null&version=1": dial unix /var/run/docker.sock: connect: permission denied
make: *** [Makefile:76: docker-build] Error 1
```

```
sudo docker-build
```

## docker の image を containerd に取り込む方法

```
# dockerからimageをexport
$ sudo docker images controller
REPOSITORY   TAG       IMAGE ID       CREATED          SIZE
controller   latest    d3c7080f44b6   13 seconds ago   50MB

$ sudo docker save --output controller:latest.tar controller:latest
```

```
# containerdにimageをimport
# containerdにはnamespaceの概念があり(k8sのnamespaceとは関係ない)、k8sはk8s.ioというnamespaceを利用している
$ sudo ctr -n k8s.io image import --base-name controller:latest controller:latest.tar
unpacking docker.io/library/controller:latest (sha256:c7f2325a15d1c6b434c02d405aad3979fd5c340e87ffd5f558b9927460f1c3f6)...done

$ sudo ctr -n k8s.io image ls
```

## 手元で実行する

```
# editでmanagerのimageをhaproxyにしてsleepさせる(プロキシできればhaproxyでなくてもよい)
$ source ~/labo/kubernetes/1.25.1/envrc
$ kubectl edit deploy -n markdown-view-system
containers:
  - command:
      - sleep
    args:
      - "9999"
    image: haproxy:2.6.6
    name: manager

$ make deploy


$ mkdir -p /tmp/k8s-webhook-server/serving-certs/
$ alias tmpcmd="kubectl exec -n markdown-view-system markdown-view-controller-manager-77b8d54774-wsrjs --"
$ tmpcmd cat /tmp/k8s-webhook-server/serving-certs/ca.crt > /tmp/k8s-webhook-server/serving-certs/ca.crt
$ tmpcmd cat /tmp/k8s-webhook-server/serving-certs/tls.crt > /tmp/k8s-webhook-server/serving-certs/tls.crt
$ tmpcmd cat /tmp/k8s-webhook-server/serving-certs/tls.key > /tmp/k8s-webhook-server/serving-certs/tls.key

$ go run . -metrics-bind-address :18080


securityContext, readynessProve, livenessProve を消す



cat << EOS > /tmp/haproxy.cfg
defaults
    timeout connect 10s
    timeout client 30s
    timeout server 30s
    log stdout format raw local0
    mode tcp
    maxconn 3000

frontend markdownview
    bind 0.0.0.0:9443
    default_backend web_servers

backend web_servers
    balance roundrobin
    server server1 192.168.10.121:9443
EOS


$ pod=`kubectl -n markdown-view-system get pod | grep controller | awk '{print $1}'`
$ kubectl -n markdown-view-system cp /tmp/haproxy.cfg $pod:/tmp/haproxy.cfg

$ kubectl exec -n markdown-view-system $pod -c manager -- haproxy -f /tmp/haproxy.cfg
```

```
$ go run . -metrics-bind-address :18080 -kubeconfig $KUBECONFIG
```

```
$ kubectl get markdownview
NAME                  REPLICAS   STATUS
markdownview-sample   1


```

```
# crd
$ kubectl get crd markdownviews.view.kubebuilder.example.com
```

```
$ kubectl get svc -n markdown-view-system
NAME                                               TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
markdown-view-controller-manager-metrics-service   ClusterIP   10.32.0.181   <none>        8443/TCP   7d1h
markdown-view-webhook-service                      ClusterIP   10.32.0.225   <none>        443/TCP    7d1h
```

```
$ kubectl port-forward --address 0.0.0.0 svc/viewer-markdownview-sample 3000:80
Forwarding from 0.0.0.0:3000 -> 3000
```

## Reconcile

- Reconcile 処理は下記のタイミングで呼び出される
  - コントローラの扱うリソースが作成、更新、削除されたとき
  - Reconcile に失敗してリクエストがキューに積まれたとき
  - コントローラの起動時
  - 外部イベントが発生したとき
  - キャッシュを再同期するとき（デフォルトでは 10 時間に一回）
- Reconcile 処理はデフォルトでは１秒間に 10 回以上実行されないように制限されています
  - また、これらのイベントが高い頻度で発生する場合は、Reconcile Loop を並列実行するように設定可能です

## テスト

envtest は etcd と kube-apiserver を立ち上げてテスト用の環境を構築します。 また環境変数 USE_EXISTING_CLUSTER を指定すれば、既存の Kubernetes クラスターを利用したテストをおこなうことも可能です。

Envtest では、etcd と kube-apiserver のみを立ち上げており、controller-manager や scheduler は動いていません。 そのため、Deployment や CronJob リソースを作成しても、Pod は作成されないので注意してください。
