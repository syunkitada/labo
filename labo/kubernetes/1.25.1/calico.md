# calico

## API server

- 今までは Calico API にアクセスするために、calicoctl が必要だったが、v3.20 からは kubectl 経由で利用できる

```
calicoctl node
calicoctl ipam
calicoctl convert
calicoctl version
```

```
$ kubectl get tigerastatus
NAME        AVAILABLE   PROGRESSING   DEGRADED   SINCE
apiserver   True        False         False      129m
calico      True        False         False      129m
```

```
$  kubectl get ippools
NAME                  AGE
default-ipv4-ippool   125m
```
