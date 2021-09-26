# frr1

- 多段で BGP をつなぎ、各ノード間で疎通が取れるようにするだけ

## 構成

```
spine1 --- leaf1 --- hv1

```

| name   | admin ip(router id) | as         |
| ------ | ------------------- | ---------- |
| hv1    | 10.1.10.1/32        | 4200110001 |
| leaf1  | 10.1.20.1/32        | 4200120001 |
| spine1 | 10.1.30.1/32        | 4200130001 |

## frr.conf メモ

- vtysh 上で、configure terminal を実行すると、config モードに移行して、コマンドによってインタラクティブに設定を行うことができる
- config モードは、exit によって離脱することができ、write memory コマンドによって、frr.conf に設定を保存できる
- frr.conf の実態はコマンドの羅列であり、これは write memory を利用して作成してもよいし、直接編集して frr に反映させてもよい
- !と＃はコメントアウト
  - vtysh で write memory すると、conf に!が書かれるが特に意味はない
  - 設定の種別ごとの区切りにのタイミングで!を挿入する
- 種別によってはインデントを空けたりもするが、可読性のためであって特に意味はない

```
# datacenter向けのprofileに設定する
# traditionalはインターネットルーティング向け
frr defaults datacenter

# (frr上の)hostnameの設定
hostname leaf1

# ログの出力先を指定
log file /var/log/frr/frr.log

!


# BGP unnumberedを利用するためのインターフェイス定義
interface leaf1-hv1-2
 ipv6 nd ra-interval 10
 no ipv6 nd suppress-ra
!


# AS(4200110001)でbgpを開始する
router bgp 4200110001

  # peerの設定
  # ADMINという名前で、peer-groupを作成
  neighbor ADMIN peer-group

  # peerの作成(ebgp)
  neighbor ADMIN remote-as external

  # BGPマルチパス設定
  bgp bestpath as-path multipath-relax

  # unnumbered を利用
  neighbor ADMIN capability extended-nexthop

  # unnumbered で利用するinterfaceを指定する
  neighbor leaf1-hv1-2 interface peer-group ADMIN

  # address-familyの定義
  # ここに定義したIPアドレスが広報される
  address-family ipv4 unicast
    # IPアドレスの静的な定義
    network 10.1.10.1/32
  exit-address-family
!

```
