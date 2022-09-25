# kube-apiserver

## api 一覧

```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:6443
CoreDNS is running at https://127.0.0.1:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

```
$ kubectl api-resources
```

```
# debug logを出す場合は、-v 6を付ける（どのエンドポイントをたたいてるかなどがわかる）
$ kubectl get pod -v 6

# -v 9を付けると、requestのheader, body、responseのheader, bodyなども表示される
$ kubectl get pod -v 9
```

```
# 認証をスキップするプロキシをローカルで起動してcurlをする
$ kubectl proxy --port=8080 &
Starting to serve on 127.0.0.1:8080

# List known groups
$ curl http://localhost:8080/

# List known versions of the `apps` group
$ curl http://localhost:8080/api

# List known resources of the `apps/v1` group
$ curl http://localhost:8080/api/v1

# Get pods
$ curl http://localhost:8080/api/v1/namespaces/default/pods

# proxyを使わなくても、以下のように--raw オプションでパスを指定してリクエストすることもできる
# GET リクエスト
$ kubectl get --raw /apis/apps/v1/namespaces/default/deployments -v 6
# POST リクエスト(-f がそのままrequest bodyになる -> jsonでリクエストしないといけない)
$ kubectl create --raw /apis/apps/v1/namespaces/default/deployments -v 6 -f resources/nginx.json
# PUT リクエスト
$ kubectl replace --raw /apis/apps/v1/namespaces/default/deployments -v 6 -f resources/nginx.json
# DELETE リクエスト
$ kubectl delete --raw /api/v1/namespaces/default/pods -v 6
```

## curl で直接叩く

```
$ curl --cacert $K8S_ASSETS_DIR/ca.pem https://127.0.0.1:6443/version
{
  "major": "",
  "minor": "",
  "gitVersion": "v0.0.0-master+$Format:%H$",
  "gitCommit": "$Format:%H$",
  "gitTreeState": "",
  "buildDate": "1970-01-01T00:00:00Z",
  "goVersion": "go1.19.1",
  "compiler": "gc",
  "platform": "linux/amd64"
}

# apiのほとんどは認証が必要なので403となります
$ curl --cacert $K8S_ASSETS_DIR/ca.pem https://127.0.0.1:6443/api/v1/namespaces
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "namespaces is forbidden: User \"system:anonymous\" cannot list resource \"namespaces\" in API group \"\" at the cluster scope",
  "reason": "Forbidden",
  "details": {
    "kind": "namespaces"
  },
  "code": 403
}

# 以下のようにクライアント証明書を指定するとアクセスできます（クライアント証明書認証）
# https://kubernetes.io/docs/reference/access-authn-authz/authentication/#x509-client-certs
$ curl --cacert $K8S_ASSETS_DIR/ca.pem --cert $K8S_ASSETS_DIR/admin.pem --key $K8S_ASSETS_DIR/admin-key.pem https://127.0.0.1:6443/api/v1/namespaces
...
```

```
# tokenの取得
$ kubectl get sa
NAME      SECRETS   AGE
default   0         3h27m

$ JWT_TOKEN_DEFAULT_DEFAULT=$(kubectl create token default)

# 叩けない
$ curl --cacert $K8S_ASSETS_DIR/ca.pem https://127.0.0.1:6443/api/v1
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "forbidden: User \"system:anonymous\" cannot get path \"/api/v1\"",
  "reason": "Forbidden",
  "details": {},
  "code": 403
}

# 叩ける
$ curl --cacert $K8S_ASSETS_DIR/ca.pem --header "Authorization: Bearer ${JWT_TOKEN_DEFAULT_DEFAULT}" https://127.0.0.1:6443/api/v1
...

# 叩けない
$ curl --cacert $K8S_ASSETS_DIR/ca.pem --header "Authorization: Bearer ${JWT_TOKEN_DEFAULT_DEFAULT}" https://127.0.0.1:6443/api/v1/namespaces
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "namespaces is forbidden: User \"system:serviceaccount:default:default\" cannot list resource \"namespaces\" in API group \"\" at the cluster scope",
  "reason": "Forbidden",
  "details": {
    "kind": "namespaces"
  },
  "code": 403
}

JWT_TOKEN_DEFAULT_DEFAULT=$(kubectl -n kube-system create token default)
```

## 拡張

- Kubernetes Custom Resources is just a way to add new HTTP endpoints to the API.
- Kubernetes Custom Controllers is a way to bind asynchronous handlers to API endpoints.
- Kubernetes Admission Webhooks is a way to bind synchronous handlers to the same API endpoints.

## controller

- https://github.com/kubernetes/community/blob/2e3d491ca40d05233362b125a0e756ad3223a51f/contributors/devel/sig-api-machinery/controllers.md

## api

- v1alpha1
  - 今後仕様が変わる場合がある
- v1beta1
  - 今後仕様が変わる場合がある
- v1
  - 安定版

## メモ

- https://iximiuz.com/en/posts/kubernetes-api-structure-and-terminology/
- https://github.com/kubernetes/sample-apiserver
