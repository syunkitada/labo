# code-generator

```
$ go install k8s.io/code-generator/cmd/deepcopy-gen@latest
$ deepcopy-gen -h
```

- https://github.com/kubernetes/gengo
- https://github.com/kubernetes/kubernetes/tree/master/staging/src/k8s.io/code-generator

```
$ ls ./staging/src/k8s.io/api/apps/v1/
doc.go  generated.pb.go  generated.proto  register.go  types.go  types_swagger_doc_generated.go  zz_generated.deepcopy.go

# exampleのコード生成
$ ./hack/update-codegen.sh
Generating deepcopy funcs
Generating defaulters
Generating conversions
Generating clientset for example:v1 example2:v1 example3.io:v1 at k8s.io/code-generator/examples/apiserver/clientset
Generating listers for example:v1 example2:v1 example3.io:v1 at k8s.io/code-generator/examples/apiserver/listers
Generating informers for example:v1 example2:v1 example3.io:v1 at k8s.io/code-generator/examples/apiserver/informers
Generating OpenAPI definitions for example:v1 example2:v1 example3.io:v1 at k8s.io/code-generator/examples/apiserver/openapi
Generating deepcopy funcs
Generating clientset for example:v1 example2:v1 at k8s.io/code-generator/examples/crd/clientset
Generating listers for example:v1 example2:v1 at k8s.io/code-generator/examples/crd/listers
Generating informers for example:v1 example2:v1 at k8s.io/code-generator/examples/crd/informers
Generating deepcopy funcs
Generating clientset for example:v1 at k8s.io/code-generator/examples/MixedCase/clientset
Generating listers for example:v1 at k8s.io/code-generator/examples/MixedCase/listers
Generating informers for example:v1 at k8s.io/code-generator/examples/MixedCase/informers
Generating deepcopy funcs
Generating clientset for example:v1 at k8s.io/code-generator/examples/HyphenGroup/clientset
Generating listers for example:v1 at k8s.io/code-generator/examples/HyphenGroup/listers
Generating informers for example:v1 at k8s.io/code-generator/examples/HyphenGroup/informers
```
