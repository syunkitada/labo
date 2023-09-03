# Custom Controller

- コントローラとは？
  - k8s では、あるリソースの状態をチェックして何らかの処理を行うプログラムをコントローラと呼びます。
    - https://github.com/kubernetes/kubernetes/tree/master/pkg/controller
    - 例
      - deployment を管理するコントローラ(Deployment Controller)は、kube-apiserver に Deployment リソースが登録されると対応する ReplicaSet リソースを新たに作成します。
      - 次に ReplicaSet を管理するコントローラ(ReplicaSet Controller)は、ReplicaSet リソースが登録されると spec.replicas に指定された 3 つの Pod を新たに作成します。
      - kube-scheduler は、kube-apiserver に Pod リソースが登録されると、Pod を配置するノードを決定し Pod の情報を更新します。
      - kubelet は、自分のノード名が記述された Pod リソースを見つけるとコンテナを立ち上げます。
  - Reconcilation Loop
    - コントローラは、リソースに記述された状態を理想とし、システムの現在の状態と比較し、その差分がなくなるように調整する処理を無限ループで実行し続けます。
    - エッジドリブントリガーとレベルドリブントリガー
      - エッジドリブントリガー: 状態が変化したイベントに応じて処理を実行すること
        - イベントをロストした場合に、あるべき状態と現在の状態がずれてしまう
      - レベルドリブントリガー: 現在の状態に応じて処理を実行すること
        - イベントをロストしても現在の状態を見て、あるべき状態に収束することが可能
    - k8s ではレベルドリブントリガーを採用しており、変化が生じた際に Reconcilation Loop によってあるべき状態へ収束させます
- k8s のリソース、コントローラはユーザが定義することができます
  - ユーザが定義したリソースをカスタムリソースと呼びます
  - ユーザが定義したコントローラをカスタムコントローラと呼びます
  - カスタムリソースとカスタムコントローラの組み合わせたものをオペレータと呼びます

## 参考

- [The Kubebuilder Book](https://book.kubebuilder.io/)
- [つくって学ぶ Kubebuilder](https://zoetrope.github.io/kubebuilder-training/)
- [Kubernetes オペレータのアンチパターン＆ベストプラクティス](https://speakerdeck.com/zoetrope/kubernetesoperetafalseantipatan-besutopurakuteisu)
  - 関連
    - [MOCO](https://github.com/cybozu-go/moco/tree/main)
      - MOCO is a MySQL operator on Kubernetes
      - コードリーディングによいかも
- [理想的な Kubernetes カスタムコントローラーの開発環境を考えた](https://engineering.mercari.com/blog/entry/20210831-f666b94b24/)

$ curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && sudo mv kubebuilder /usr/local/bin/

TODO

- kubectl flame
- tracing を使ってみる
  https://kubernetes.io/docs/concepts/cluster-administration/system-traces/
- watch の実装を見てみる
  https://kubernetes.io/docs/reference/using-api/
