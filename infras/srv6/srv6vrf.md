# srv6vrf

## 環境準備

- SRv6, VRF を利用するには、Kernel のビルドオプションに以下が含まれている必要があります

```
$ egrep 'SEG6|VRF' /boot/config-`uname -r`
# srv6を使うために必要なビルドオプション
CONFIG_IPV6_SEG6_LWTUNNEL=y
CONFIG_IPV6_SEG6_HMAC=y
CONFIG_IPV6_SEG6_BPF=y

# VRFを使うために必要なビルドオプション
CONFIG_NET_VRF=y
```

## Kernel のビルド方法

```
$ sudo apt-get update
$ sudo apt install -y build-essential bc bison flex libelf-dev libssl-dev libncurses5-dev
```

```
$ wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.15.120.tar.xz
$ tar xf linux-5.15.120.tar.xz
```

```
$ cd linux-5.15.120
$ cp /boot/config-`uname -r` .config

sed -i 's/CONFIG_SYSTEM_TRUSTED_KEYS=".*"/CONFIG_SYSTEM_TRUSTED_KEYS=""/g' .config
sed -i 's/CONFIG_SYSTEM_REVOCATION_KEYS=".*"/CONFIG_SYSTEM_REVOCATION_KEYS=""/g' .config
sed -i 's/CONFIG_DEBUG_INFO_DWARF4=.*/CONFIG_DEBUG_INFO_DWARF4=n/g' .config
sed -i 's/CONFIG_DEBUG_INFO_BTF=.*/CONFIG_DEBUG_INFO_BTF=n/g' .config
sed -i 's/CONFIG_NET_VRF=.*/CONFIG_NET_VRF=y/g' .config
sed -i 's/CONFIG_IPV6_SEG6_LWTUNNEL=.*/CONFIG_IPV6_SEG6_LWTUNNEL=y/g' .config
sed -i 's/CONFIG_IPV6_SEG6_HMAC=.*/CONFIG_IPV6_SEG6_HMAC=y/g' .config
sed -i 's/CONFIG_IPV6_SEG6_BPF=.*/CONFIG_IPV6_SEG6_BPF=y/g' .config

$ egrep 'SEG6|VRF' .config
```

```
# makeでビルド
# オプションはEnter連打する
$ make

$ sudo make modules_install
$ sudo make install
```
