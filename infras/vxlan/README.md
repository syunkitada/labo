# VXLAN

- VXLAN は、L3 ネットワーク上に仮想的な L2 ネットワークを構築するためのトンネリングプロトコルです
  - 他のトンネリングプロトコルと違い、L2 のイーサネットフレームをカプセル化する
  - VXLAN は 24 ビットの ID を持つことができる
    - ちなみに VLAN は 12 ビット
- VTEP(VXLAN Tunneling End Point)
  - トンネリングのエンドポイントのこと
  - VTEP は、L2 通信を仮想化するために、お互いの存在や、その配下のノード情報をやり取りする必要がある
    - 通常の L2 通信は、ARP パケットをブロードキャストして、宛先 IP アドレスを持ったサーバの MAC を取得して、その MAC あてでパケットを送信します
    - VTEP は、何らかの方法で互いの配下の MAC を共有して ARP を解決できるようにして、その MAC アドレス宛ての通信をカプセル化して担当する VTEP に送信します
  - VTEP の実装はまちまちで、VXLAN を接続する VTEP 同士は同じ仕組みを扱える必要がある
  - 参考
    - [Flannel の VXLAN バックエンドの仕組み](https://enakai00.hatenablog.com/entry/2015/04/02/173739)
- VXLAN vs GRE
  - https://www.reddit.com/r/networking/comments/4bko87/vxlan_vs_gre/
  - VXLAN は UDP 上に実装されてるので ECMP できるが、GRE はできない（実装によってはできる？）
    - VXLAN なら Gateway をスケールできる？
