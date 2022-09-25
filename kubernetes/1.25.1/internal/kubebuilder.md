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

## 開発メモ

- 開発時に docker のイメージを毎回ビルドしなおす必要があるのはどうにかならないのか？
