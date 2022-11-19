# sample-xxx

## sample-controller

- https://github.com/kubernetes/sample-controller

コントローラの起動

```
$ git clone https://github.com/kubernetes/sample-controller.git -b release-1.25
$ cd sample-controller

$ go run . -h
...

$ source ~/labo/kubernetes/1.25.1/envrc
$ go run . -kubeconfig $KUBECONFIG
...
```

サンプルのリソースを作成

```
# create a CustomResourceDefinition
kubectl create -f artifacts/examples/crd-status-subresource.yaml

# create a custom resource of type Foo
kubectl create -f artifacts/examples/example-foo.yaml

# check deployments created through the custom resource
kubectl get deployments

# cleanup
kubectl delete crd foos.samplecontroller.k8s.io
```

## sample-apiserver

- https://github.com/kubernetes/sample-apiserver

API の起動

```
$ git clone https://github.com/kubernetes/sample-apiserver.git
$ cd sample-apiserver

$ go run . -h
...
```

```
$ go run . --secure-port 8443 --etcd-servers http://127.0.0.1:2379 --v=7 \
   --client-ca-file=${VAR_DIR}/ca.pem \
   --kubeconfig=${VAR_DIR}/kube-controller-manager.kubeconfig \
   --authentication-kubeconfig ${VAR_DIR}/kube-controller-manager.kubeconfig \
   --authorization-kubeconfig ${VAR_DIR}/kube-controller-manager.kubeconfig
```
