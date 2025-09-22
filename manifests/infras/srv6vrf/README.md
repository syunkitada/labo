# srv6vrf

## 環境準備

- SRv6, VRF を利用するには、Kernel のビルドオプションに以下が含まれている必要があります
- Ubuntu 22.04.4 LTS では、デフォルトで含まれています

```
$ egrep 'SEG6|VRF' /boot/config-`uname -r`
# srv6を使うために必要なビルドオプション
CONFIG_IPV6_SEG6_LWTUNNEL=y
CONFIG_IPV6_SEG6_HMAC=y
CONFIG_IPV6_SEG6_BPF=y

# VRFを使うために必要なモジュール
CONFIG_NET_VRF=m
```

```
y  =  yes (always installed)
m  =  loadable module (can install and uninstall as you wish)
n  =  no (never installed)
```

```
$ sudo modprobe vrf

$ lsmod | grep vrf
vrf                    32768  0
```
