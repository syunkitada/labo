# Fake Client

- [fake-client](https://github.com/kubernetes/client-go/tree/master/examples/fake-client)の写経+α

```
$ go test -v ./...
=== RUN   TestFakeClient
    main_test.go:44: pod added: test-ns/my-pod
    main_test.go:69: Got pod from channel: test-ns/my-pod
--- PASS: TestFakeClient (0.10s)
PASS
ok      github.com/syunkitada/labo/kubernetes/1.25.1/experimental-codes/client-go-fake-client   0.122s
```
