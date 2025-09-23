# frr

## AS 番号

- 一つの運用ポリシーを持ったネットワークのかたまり

- 2 バイト AS
  - 範囲: 0 – 65535
  - プライベート AS: 64512 – 65534
- 4 バイト AS
  - 範囲: 0 - 4294967295
  - ICANN 予約分: 0, 64496 - 64511, 65535 - 131071, 4294967295
  - プライベート AS: 64512 – 65534, 4200000000 - 4294967294

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

BGP において、BGP Extended Next Hop Encoding(RFC 5549)を有効にする設定です。

通常、BGP の NLRI (経路情報) では、IPv4 アドレスファミリーには IPv4 ネクストホップ、IPv6 アドレスファミリーには IPv6 ネクストホップしか載せられません。

- IPv4 の経路には → IPv4 nexthop
- IPv6 の経路には → IPv6 nexthop

という制約がありました。

これを解決するのが BGP Extended Next Hop Encoding で、これを有効にすると、capability を OPEN メッセージで通知するようになり、IPv6 ピアセッション上で Ipv4 の経路を広報できるようになります。

## neighbor RR ebgp-multihop 254

## neighbor PEER update-source <IFNAME|ADDRESS>

- [neighbor PEER update-source <IFNAME|ADDRESS>](https://docs.frrouting.org/en/stable-10.4/bgp.html#clicmd-neighbor-PEER-update-source-IFNAME-ADDRESS)

その BGP ピアに対して使う「自分側の送信元 IP アドレス」を指定する設定です。

- なぜ必要か？
  - デフォルトでは BGP は「隣接インターフェースのアドレス」を送信元にします。
  - でも、物理インターフェースのアドレスを使うと、以下のような問題が起こります：
    - リンクが 1 本でもダウンするとセッションが切れる
    - 冗長化した物理リンクを活かせない
  - これを避けるために、loopback アドレス（常に UP している論理インターフェース）を送信元にするのが一般的です。

## ルートリフレクタ(RR)

- [BGP ルートリフレクタ](https://docs.frrouting.org/en/latest/bgp.html#bgp-route-reflector)
- RR は、iBGP のメッシュ接続を避けるための仕組みです。
  - 通常、iBGP (同一 AS 内の BGP) では フルメッシュ接続が必要です。
  - N 台のルータがある場合、iBGP セッションは N\*(N-1)/2 本必要になる。
  - 規模が大きくなると現実的でない。
  - そこで Route Reflector (RR) という仕組みが導入されました。
  - RR は「反射器」として動作し、受け取った BGP ルートをクライアントに再配布します。
  - これにより、すべてのルータがフルメッシュでつながる必要がなくなります。
- eBGP には RR の概念はありません

## Route Distinguisher (RD) と RT (Route Target)

- RD
  - VPN ごとに同じアドレス空間（例: 192.168.1.0/24）を区別するための「識別子」です。
  - 同一プレフィックスでも VRF ごとに一意に識別できるようにします。
  - なぜ必要か？
    - 複数の顧客が同じプライベートアドレスを使っていると、単純に BGP で流すと「区別がつかない」。
    - そこで、RD をアドレスに付与して一意な VPNv4/VPNv6 アドレスを作る。
      - 例:
        - 顧客 A: RD 65000:1 + 192.168.1.0/24 → RD=65000:1:192.168.1.0/24
        - 顧客 B: RD 65000:2 + 192.168.1.0/24 → RD=65000:2:192.168.1.0/24
    - こうすると BGP は「別物のルート」として扱える。
  - 形式: 64bit の値
    - よく使われる表記は ASN:番号 または IP アドレス:番号です
    - Type 0 (ASN2byte:番号)
      - 上位 16bit = 2 バイト ASN
      - 下位 32bit = 任意の番号
      - 表記例: 65000:100
      - 制約: ASN が 16bit (1–65535) の場合に使用
    - Type 1 (IPv4 アドレス:番号)
      - 上位 32bit = IPv4 アドレス
      - 下位 16bit = 任意の番号(1-65535)
      - 表記例: 192.0.2.1:200
      - 制約: IPv4 アドレス表記に従う（RFC1918 も可だが管理上は注意）
    - Type 2 (ASN4byte:番号)
      - 上位 32bit = 4 バイト ASN (1–4294967295)
      - 下位 16bit = 任意の番号(1-65535)
      - 表記例: 4200000000:300
- RT
  - VPNv4 プレフィックスにさらにアトリビュートとして、RT（Route Target）を付加して通知します。
  - 受信側の PE ルータはこの RT の情報をもとに、受信した経路情報を該当する VRF に挿入するかしないかを制御できます。
  - 形式: 64bit の値
    - RD と同じ形式で ASN:番号 または IP アドレス:番号 で表記するのが一般的です
- 動作イメージ
  1. CE（顧客ルータ）から PE（プロバイダエッジ）へルートが入る
  2. PE はそのルートに RD を付けて「一意な VPNv4/VPNv6 アドレス」に変換
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
