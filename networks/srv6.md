# SRv6

## Segment Routing(SR) アーキテクチャ

- ネットワークを Segment で表現し、送信元が Segment のリストをパケットに埋め込み転送する（ソースルーティング）
- MPLS や IPv6 といったデータプレーンへの適用が用意
  - MPLS を利用したものを SR-MPLS(MPLS 対応ルータが必要)、IPv6 を利用したものを SRv6(IPv6 対応ルータが必要)と呼ぶ
  - SRv6 のほうが導入条件が低く、採用実績も多い

## 用語

- Segment
  - 流入してくるパケットに対してノードが実行する処理のこと
- SID(Segment Identifier)
  - Segment に割り当てられる Segment 識別子
- Segment List
  - Segment Routing の経路に沿って並べられた Segment のリスト
- SR Domain
  - Segment Routing に参加するノード(SR ノード)の集まり
- Active Segment
  - Segment List のうち、パケット処理のためのそのノードによって実施される Segment のこと
- Global Segment
  - SR Domain 内のすべてのノードが認識する Segment
  - SID は SR Domain 内でユニーク
- Local Segment
  - そのノード自身だけが認識する Segment
  - L2 の概念に近い
  - SID はノード内でユニーク
- Node Segment
  - Global Segment であり、その SID は Domain 内でユニーク
  - この SID のことを Node SID と呼ぶ
- Adjacency Segment
  - Local Segment であり、その SID は Local 内でユニーク
  - この SID のことを Adjacency SID と呼ぶ
- Prefix Segment
  - 本質的には Node Sgment と同じもの
  - この Segment の ID を Prefix SID と呼ぶ
    - ノード A からみて、ノード B の Node Segment が Prefix Segment となる
    - ノード A からみて、ノード B の Node SID が Prefix SID となる
  - SRv6 ではこの Prefix SID と IPv6 Prefix を同じとすることができる(IPv6 でリーチできる）
  - IGP Prefix Segment と BGP Prefix Segment の２種類があり、これらをまとめて Prefix Segment と呼ぶ
    - IGP で広報されるか、BGP で広報されるかの違い
- BGP Peering Segment
  - BGP-LS によって広報される
  - 特定の BGP peer に転送する
  - ボーダーで使われる？
- SR Global Block(SRGB)
  - SR ノードが Global Segment 向けに確保する領域
- Binding-SID
  - 2 つのノード間を特別につなげるときに使うもの(VPN, TE など)
  - 特定の通信を識別して中身を見れたりする？
- SONiC(Software for Open Networking in the Cloud)
  - ホワイトボックススイッチ用の OSS の NOS
    - 厳密には ONL 上で動作するソフトウェア群
    - Microsoft が公開したソースコードが母体
    - BGP や LLDP、データベースなどのアプリケーションはコンテナ化されている
  - 構成ソフトウェア群
    - OS: Open Network Linux
    - L3: FRR
    - DB: Redis
    - syncd
      - SAI(Switch Abstraction Interface)
        - スイッチチップの差分を隠ぺいするためのインターフェイス
        - マルチベンダ対応を実現
          - Broadcom, Barefoot, Mellanox など複数のチップベンダのスイッチをサポート
  - データプレーンプログラム言語として P4 が利用できる
- P4(Programming Protocol-independent Packet Processor)
  - パケットのパイプライン処理（パーサー、マッチアクションテーブル、デパーサー）を記述するためのプログラミング言語
  - P4 でプログラミングしたデータプレーンをハードウェアにて動作させることが可能
    - Barefoot Tofino チップ（スイッチ用）、Netcope P4 コンパイラ（FPGA NIC 用）など
  - 参考
    - https://p4.org/p4-spec/docs/P4-16-v1.2.1.pdf

## SRv6: Segment Routing over IPv6

- IPv6 拡張ヘッダを利用（Segment Routing Header: SRH と呼ぶ）
  - ソースルーティングであり、通るノード分 IPv6 Header を SRH に付与して送信する
  - 拡張ヘッダの Length は可変であるため、SRH 内で Segment List を通過ノード分定義できる
  - Segments Left
    - 処理が残ってる Segment の数（ノードを通過するときにデクリメントされる）
  - Segment List
    - 経由する SRv6 ノードの SID のリスト
  - SRv6 は Endpoint と経由する Node の数分、SRH(128bit)を付与するため、トラフィックの高負荷が懸念されている
    - この問題を解決するため、SRv6+(Segment Routing Mapped To IPv6(SRm6))の仕様について議論されている
    - Node 通過時に Segment List のうち自身のノードの SID は不要となるためこれを削る処理(Reduce)もある
- SID
  - SID は、IPv6 Prefix が Prefix SID として広報され使われる
  - 残りのビットは、ノードで実行する関数（FUNC)、関数の引数（ARG）として利用できる(SRv6 Network Function)
- SRv6-VPN/EVPN
  - DC ネットワークでは SRv6-VPN を利用して、SD-WAN や SD-LAN の実現が可能
  - この原理を利用して両端の Customer Edge の mac を広報する EVPN も実現可能
  - MP-BGP で VPN 情報を広報し、SRv6 ネットワーク上で Overlay ネットワークを構築
- SRv6 ノード
  - Source SR Node
    - SRv6 パケットの生成
    - SRv6 パケットのカプセル化を行い、パケットを送信
  - Transit Node
    - SR の処理はせずに IPv6 で転送する
    - 中継ノードは、SR をサポートしている必要はなく、IPv6 が利用できればよい
  - SR Segment Endpoint Node
    - Segment の処理
    - SRH を Loopup し、Segment に設定された Function を実施
- End Function
  - Endpoinnt Node において実施される Function
  - End.DX4, End.DX6
    - IPv4/IPv6 通信を SRv6 で Decap する
  - End.DT4, End.DT6
    - Decap した後さらにルーティングテーブルを Lookup する
  - 参考
    - https://datatracker.ietf.org/doc/html/draft-ietf-spring-srv6-network-programming-28#page-10
- VPN における例
  - 通信元は IPv4 で通信可能な末端ノードで IPv4 通信を SRv6 で Encap し、宛先に到達可能な末端ノードへ送る
  - 末端ノードではこれを End.DX4 によって Decap し宛先へ IPv4 としてフォワードする
  - また、End.DT4 を利用すると、VPN をテナントごとに分け、DECAP 処理後にそれぞれのテナントごとに定義されたルーティングテーブルを Lookup させることもできる
- SRv6 を使った仮想ネットワーク
  - Overlay: SRv6-VPN
  - Underlay: SRv6 IS-ISv6
- SRv6 を使った仮想ネットワーク 2
  - Overlay: SRv6 MP-BGP
  - Underlay: SRv6 OSPF6
- サービスチェイニング
  - SRv6 では経由するノードをソース側で指定できるので、特定のサービス提供するノードを明示的に経由させることもできる
  - このような各種サービスを行うノードを数珠つなぎで経由させることをサービスチェイニングと呼ぶ

## 参考

- [Segment Routing チュートリアル:20170718](https://www.janog.gr.jp/meeting/janog40/application/files/2415/0051/7614/janog40-sr-kamata-takeda-00.pdf)
- [SONiC + P4 によるマルチテナント SRv6 サービスチェイニングの実現](https://www.janog.gr.jp/meeting/janog46/wp-content/uploads/2020/06/JANOG46_SONiCSRv6P4_v.0.14.pdf)
