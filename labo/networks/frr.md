# frr

## BGP 設定メモ

- [BGP ピアの設定](http://docs.frrouting.org/en/latest/bgp.html#bgp-neighbor)

```
neighbor <address|interface> remote-as <asn>
```

対向の BGP ルータ (Neighbor) の IP アドレスと AS 番号(asn)を指定します。

asn は external または internal も指定可能です。

internal を指定した場合は、internal BGP (iBGP) による接続が想定され、Neighbor の AS 番号が、自分の AS 番号と同じであれば、接続できます。
external を指定した場合は、external BGP (eBGP) による接続を想定され、AS 番号が違う場合に接続できる設定になります。

## capability extended-nexthop

- [BGP capability extended-nexthop](https://docs.frrouting.org/en/latest/bgp.html#clicmd-neighbor-PEER-capability-extended-nexthop)

```
neighbor {{ client.ip }} capability extended-nexthop
```

BGPにおいて、BGP Extended Next Hop Encoding(RFC 5549)を有効にする設定です。

通常、BGPのNLRI (経路情報) では、IPv4アドレスファミリーにはIPv4ネクストホップ、IPv6アドレスファミリーにはIPv6ネクストホップしか載せられません。

- IPv4の経路には → IPv4 nexthop
- IPv6の経路には → IPv6 nexthop

という制約がありました。

これを解決するのがBGP Extended Next Hop Encodingで、これを有効にすると、capability を OPEN メッセージで通知するようになり、IPv6ピアセッション上でIpv4の経路を広報できるようになります。

## neighbor RR ebgp-multihop 254

## neighbor PEER update-source <IFNAME|ADDRESS>

- [neighbor PEER update-source <IFNAME|ADDRESS>](https://docs.frrouting.org/en/stable-10.4/bgp.html#clicmd-neighbor-PEER-update-source-IFNAME-ADDRESS)

その BGP ピアに対して使う「自分側の送信元 IP アドレス」を指定する設定です。

- なぜ必要か？
  - デフォルトでは BGP は「隣接インターフェースのアドレス」を送信元にします。
  - でも、物理インターフェースのアドレスを使うと、以下のような問題が起こります：
    - リンクが1本でもダウンするとセッションが切れる
    - 冗長化した物理リンクを活かせない
  - これを避けるために、loopback アドレス（常にUPしている論理インターフェース）を送信元にするのが一般的です。

## ルートリフレクタ(RR)

- [BGP ルートリフレクタ](https://docs.frrouting.org/en/latest/bgp.html#bgp-route-reflector)
- RRは、iBGPのメッシュ接続を避けるための仕組みです。
  - 通常、iBGP (同一 AS 内の BGP) では フルメッシュ接続が必要です。
  - N 台のルータがある場合、iBGP セッションは N\*(N-1)/2 本必要になる。
  - 規模が大きくなると現実的でない。
  - そこで Route Reflector (RR) という仕組みが導入されました。
  - RR は「反射器」として動作し、受け取った BGP ルートをクライアントに再配布します。
  - これにより、すべてのルータがフルメッシュでつながる必要がなくなります。
- eBGPにはRRの概念はありません

## Route Distinguisher (RD) と RT (Route Target)

- RD
  - VPNごとに同じアドレス空間（例: 192.168.1.0/24）を区別するための「識別子」です。
  - 同一プレフィックスでもVRFごとに一意に識別できるようにします。
  - なぜ必要か？
    - 複数の顧客が同じプライベートアドレスを使っていると、単純にBGPで流すと「区別がつかない」。
    - そこで、RDをアドレスに付与して一意なVPNv4/VPNv6アドレスを作る。
      - 例:
        - 顧客A: RD 65000:1 + 192.168.1.0/24 → RD=65000:1:192.168.1.0/24
        - 顧客B: RD 65000:2 + 192.168.1.0/24 → RD=65000:2:192.168.1.0/24
    - こうするとBGPは「別物のルート」として扱える。
  - 形式: 64bit の値
    - よく使われる表記は ASN:番号 または IPアドレス:番号です
    - Type 0 (ASN2byte:番号)
      - 上位16bit = 2バイト ASN
      - 下位32bit = 任意の番号
      - 表記例: 65000:100
      - 制約: ASN が 16bit (1–65535) の場合に使用
    - Type 1 (IPv4アドレス:番号)
      - 上位32bit = IPv4 アドレス
      - 下位16bit = 任意の番号(1-65535)
      - 表記例: 192.0.2.1:200
      - 制約: IPv4 アドレス表記に従う（RFC1918も可だが管理上は注意）
    - Type 2 (ASN4byte:番号)
      - 上位32bit = 4バイト ASN (1–4294967295)
      - 下位16bit = 任意の番号(1-65535)
      - 表記例: 4200000000:300
- RT
  - VPNv4プレフィックスにさらにアトリビュートとして、RT（Route Target）を付加して通知します。
  - 受信側のPEルータはこのRTの情報をもとに、受信した経路情報を該当するVRFに挿入するかしないかを制御できます。
  - 形式: 64bit の値
    - RDと同じ形式で ASN:番号 または IPアドレス:番号 で表記するのが一般的です
- 動作イメージ
  1. CE（顧客ルータ）から PE（プロバイダエッジ）へルートが入る
  2. PE はそのルートに RD を付けて「一意なVPNv4/VPNv6アドレス」に変換
  3. さらに、そのルートに Export RT を付与して BGP で配布
  4. 受け取った PE は自分の VRF に設定された Import RT と照合
  5. 一致すれば VRF にインストール
  6. 一致しなければ捨てる

例

```
###################################################
# BGP VRFs
###################################################
router bgp 4201774595 vrf vrf50
  bgp router-id 10.10.20.3
  no bgp ebgp-requires-policy
  sid vpn per-vrf export auto

  address-family ipv4 unicast
    rd vpn export 65000:50
    rt vpn both 65000:50
    import vpn
    export vpn
    redistribute kernel
  exit-address-family
!
router bgp 4201774595 vrf vrf51
  bgp router-id 10.10.20.3
  no bgp ebgp-requires-policy
  sid vpn per-vrf export auto

  address-family ipv4 unicast
    rd vpn export 65000:51
    rt vpn both 65000:51
    import vpn
    export vpn
    redistribute kernel
  exit-address-family
!
```
