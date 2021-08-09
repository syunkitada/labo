# Kubernetes

## セットアップ手順

```
./00_install_pkgs.sh
./10_create_assets.sh `hostname` 192.168.100.2
./20_setup_etcd.sh `hostname` 192.168.100.2
./31_setup_kube-apiserver.sh 192.168.100.2
./31_setup_kube-apiserver.sh 192.168.100.2
./32_setup_kube-controller-manager.sh
./33_setup_kube-scheduler.sh
./34_setup_auth.sh
./40_setup_containerd.sh
./41_setup_kubelet.sh `hostname`
./50_setup_dns.sh
./60_setup_calico.sh
```

## 確認

```
$ export KUBECONFIG=~/k8s-assets/admin.kubeconfig

$ kubectl get node

$ kubectl apply -f resources/nginx.yaml

...
```
