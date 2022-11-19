# kubernetes-1.25.1

- シングルノードを想定します
- kubernetes はソースコードから起動します

## セットアップ手順

```
NODE_IP=xxx.xxx.xxx.xxx

./00_git_clone.sh
./00_install_pkgs.sh
./10_create_assets.sh `hostname` $NODE_IP
./20_setup_etcd.sh `hostname`
./31_setup_kube-apiserver.sh $NODE_IP
./32_setup_kube-controller-manager.sh
./33_setup_kube-scheduler.sh
./34_setup_auth.sh
./40_setup_containerd.sh
./41_setup_kubelet.sh `hostname`
./42_setup_kube-proxy.sh
./50_setup_dns.sh
./60_setup_calico.sh
```

## 動作確認

```
$ source envrc

$ kubectl create -f resources/nginx.yaml
deployment.apps/nginx-deployment created

$ kubectl get pod -o wide
NAME                               READY   STATUS    RESTARTS   AGE   IP         NODE            NOMINATED NODE   READINESS GATES
nginx-deployment-cd55c47f5-64lmt   1/1     Running   0          74s   10.0.0.8   hoge            <none>           <none>

$ curl 10.0.0.8
html..
```

## トラブルーシューティング: pod の log を取得が認可されてない場合

- 認可するように rbac を設定する

```
$ kubectl logs nginx-deployment-595cbd599d-jr9nm
Error from server (Forbidden): Forbidden (user=kubernetes, verb=get, resource=nodes, subresource=proxy) ( pods/log nginx-deployment-595cbd599d-jr9nm)

$ kubectl apply -f resources/apiserver-to-kubelet-rbac.yaml
```

```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:kube-apiserver-to-kubelet
rules:
  - apiGroups:
      - ""
    resources:
      - nodes/proxy
      - nodes/stats
      - nodes/log
      - nodes/spec
      - nodes/metrics
      - pods/log
    verbs:
      - "*"

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: system:kube-apiserver
  namespace: ""
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:kube-apiserver-to-kubelet
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: kubernetes
```
