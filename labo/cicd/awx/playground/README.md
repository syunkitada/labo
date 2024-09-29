# AWX

Login to http://192.168.10.121:32000/#/login

usernameは、admin

passwordは、以下のコマンドで確認する

```
$ kubectl get secret awx-demo-admin-password -o jsonpath="{.data.password}" | base64 --decode ; echo
```
