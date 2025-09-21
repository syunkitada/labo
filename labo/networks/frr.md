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
