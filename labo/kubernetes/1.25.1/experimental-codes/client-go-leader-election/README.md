# leader-election

- [leader-election](https://github.com/kubernetes/client-go/tree/master/examples/leader-election)の写経+α

```
# first terminal
$ go run main.go -kubeconfig=$KUBECONFIG -logtostderr=true -lease-lock-name=example -lease-lock-namespace=default -id=1

# second terminal
$ go run main.go -kubeconfig=$KUBECONFIG -logtostderr=true -lease-lock-name=example -lease-lock-namespace=default -id=2

# third terminal
$ go run main.go -kubeconfig=$KUBECONFIG -logtostderr=true -lease-lock-name=example -lease-lock-namespace=default -id=3
```
