# tuning

これは雑多すぎて、参考にしないほうがいい
そのうちまとめる

## Redhat tuning

https://access.redhat.com/documentation/ja-JP/Red_Hat_Enterprise_Linux/6/html/Performance_Tuning_Guide/index.html
https://access.redhat.com/documentation/ja-JP/Red_Hat_Enterprise_Linux/7/html/Performance_Tuning_Guide/index.html

## Redhat vitualization tuning

https://access.redhat.com/documentation/ja-JP/Red_Hat_Enterprise_Linux/6/html/Virtualization_Tuning_and_Optimization_Guide/index.html
https://access.redhat.com/documentation/ja-JP/Red_Hat_Enterprise_Linux/7/html/Virtualization_Tuning_and_Optimization_Guide/index.html

## Ubuntu

http://www.slideshare.net/janghoonsim/kvm-performance-optimization-for-ubuntu?qid=fb99f565-8ae4-44d3-9b58-8d8487197566&v=&b=&from_search=3

## CPU

- https://libvirt.org/formatdomain.html#elementsCPUTuning

### 割り込み仮想化

- 解説記事
  - [2025: VA Linux エンジニアブログ: 新 Linux カーネル解読室 - KVM (概要)](https://www.valinux.co.jp/blog/entry/20251204)
  - [2025: Oracle Linux Blog: How to enable AMD AVIC and speed up your VMs](https://blogs.oracle.com/linux/amd-avic)

## Disk

### cachemode の種類

| cache mode   | host page cache | disk write cache | no flush |
| ------------ | --------------- | ---------------- | -------- |
| directsync   |                 |                  |          |
| writethrough | o               |                  |          |
| none         |                 | o                |          |
| writeback    | o               | o                |          |
| unsafe       | o               | o                | o        |

- host page cache
  - qemu が Disk を open するときに O_DIRECT フラグをつけるかどうか
- disk write cache
  - virtio-blk デバイスの持つ cache
    - 通常の HDD なども 32MB や 64MB の cache を持っており、それと同じようなもの
  - qemu の中では、このキャッシュを使うかどうかで flush(fdatasync)のタイミングが異なる
    - キャッシュ有効時
      - 仮想マシン OS から flush 要求があった時に qemu が flush(fdatasync)する
    - キャッシュ無効時
      - 仮想マシンの disk write のたびに qemu が flush(fdatasync)する
- no flush
  - cache を disk に flush するのを無効化する

### cachemode の選定

- directsync
  - 物理環境と同程度の安全性が欲しい場合
  - データベースシステムなど、ファイルの不整合が許容できないところで利用するのが良い
  - しかし、IO 性能は劣化するため DISK 性能を最大限利用したい場合には不向き、またそのようなシステムで VM は利用すべきではない
- none
  - メモリ消費量はほどほどに抑え、性能もある程度確保したい場合
  - 1 つ HV に大量の VM を集約する場合はこれがよい
- writeback
  - 広大なホストのページキャッシュを利用し、性能を出したい場合
  - 1 つの HV に少量の VM を集約し、高性能 VM を提供する場合はこれがよい

### disk type

- raw
  - ただのファイル
- qcow2

  - 機能
    - sparce space
      - 仮想ディスクが必要とした部分だけ書き込む
    - snapshot
    - linked file
      - ベースファイルをリンクして、追加分だけを書き込む
    - AES 暗号化
    - 圧縮(zlib)

- https://serverfault.com/questions/677639/which-is-better-image-format-raw-or-qcow2-to-use-as-a-baseimage-for-other-vms
- https://www.jamescoyle.net/how-to/1810-qcow2-disk-images-and-performance

### disk io

- IO に制限をかける
  - [Libvirt: Block I/O Tuning](https://libvirt.org/formatdomain.html#block-i-o-tuning)
- IO Thread について
  - [2024: RedHat Developer: Scaling virtio-blk disk I/O with IOThread Virtqueue Mapping](https://developers.redhat.com/articles/2024/09/05/scaling-virtio-blk-disk-io-iothread-virtqueue-mapping#performance)
    - IO Thread を割り当てることで、ディスクがサチるまで IO 性能を上げることができる
    - 関連資料
      - [2024: RedHat Developer: Virtualized database I/O performance improvements in RHEL 9.4](https://developers.redhat.com/articles/2024/09/10/virtualized-database-io-performance-improvements-rhel-94)
        - データベースのワークロードでの検証結果が乗っている
  - [2024: Stefan Hajnoczi Blog: QEMU AioContext removal and how it was done](https://blog.vmsplice.net/2024/01/qemu-aiocontext-removal-and-how-it-was.html)
    - Big QEMU Lock、IO Thread、AioContext の話
  - [2023: VA Linux エンジニアブログ: Qemu のしくみ (の一部)](https://www.valinux.co.jp/blog/entry/20230112)
    - Big QEMU Lock、IO Thread、AioContext の話
  - [2024: Oracle Linux Blog: Improve virtio-blk device performance using iothread-vq-mapping](https://blogs.oracle.com/linux/virtioblk-using-iothread-vq-mapping)
  - [2025: Oracle Linux Blog: Improve virtio-scsi device performance using iothread-vq-mapping](https://blogs.oracle.com/linux/virtio-scsi-device-using-iothread-vq-mapping)
- virtio-blk と virtio-scsi
  - virtio-blk
    - ブロックデバイスの準仮想化インターフェイス
    - vda, vdb ... のようにデバイス名が付与される
    - PCI スロットに直接接続されたデバイスとして動作するため、PCI スロット数の制約を受ける（最大 28 デバイス）
    - ホットスワップ非対応
  - virtio-scsi
    - SCSI デバイスの準仮想化インターフェイス
    - sda, sdb ... のようにデバイス名が付与される
    - SCSI コントローラとして動作し、その下に数百のディスクを接続できる
    - ホットスワップ対応
  - 性能の違い
    - virtio-blk のほうが scsi のレイヤ分だけレイテンシが低い
  - 性能重視なら virtio-blk、機能重視なら virtio-scsi を選ぶと良い

### Virtio のキュー

- virtqueue = vCPU 数の場合、各 vCPU ごとに virtqueu が割り当てられる
- virtqueue = 1 の場合は一つのキューを各 CPU が共有することになる

virtqueue の確認方法

```
$ virsh qemu-monitor-command 6 --hmp "info virtio"
/machine/peripheral/balloon0/virtio-backend [virtio-balloon]
/machine/peripheral/virtio-disk0/virtio-backend [virtio-blk]
/machine/peripheral/net0/virtio-backend [virtio-net]
```

```
$ virsh qemu-monitor-command 6 --hmp "info virtio-status /machine/peripheral/virtio-disk0/virtio-backend"
/machine/peripheral/virtio-disk0/virtio-backend:
  device_name:             virtio-blk
  device_id:               2
  vhost_started:           false
  bus_name:                (null)
  broken:                  false
  disabled:                false
  disable_legacy_check:    false
  started:                 true
  use_started:             true
  start_on_kick:           false
  use_guest_notifier_mask: true
  vm_running:              true
  num_vqs:                 4  <-- 4 つのキューがある
  queue_sel:               3
  isr:                     1
  endianness:              little
  status:
  ...
```

```
$ virsh qemu-monitor-command  6 --hmp "info virtio-queue-status /machine/peripheral/virtio-disk0/virtio-backend 0"
/machine/peripheral/virtio-disk0/virtio-backend:
  device_name:          virtio-blk
  queue_index:          0
  inuse:                0
  used_idx:             60079
  signalled_used:       60079
  signalled_used_valid: true
  last_avail_idx:       60079
  shadow_avail_idx:     60079
  VRing:
    num:          256
    num_default:  256
    align:        4096
    desc:         0x000000010c594000
    avail:        0x000000010c595000
    used:         0x000000010c595240
```

## Network

### multiqueue のサポート

```bash
<interface type='bridge'>
    <driver name='vhost' queues='2'/>
    ...
</interface>

$ cat /proc/interrupts
# nic=2, queues=1
 24:          0          0          0          0   PCI-MSI 32768-edge      virtio0-config
 25:        620          0       1875          0   PCI-MSI 32769-edge      virtio0-input.0
 26:          1          0          0          0   PCI-MSI 32770-edge      virtio0-output.0
 27:          0          0          0          0   PCI-MSI 49152-edge      virtio1-config
 28:          1          0          0          0   PCI-MSI 49153-edge      virtio1-input.0
 29:          0          0          0          0   PCI-MSI 49154-edge      virtio1-output.0

# nic=2, queues=2
 24:          0          0          0          0   PCI-MSI 32768-edge      virtio0-config
 25:       1671          0          0       3200   PCI-MSI 32769-edge      virtio0-input.0
 26:          1          0          0          0   PCI-MSI 32770-edge      virtio0-output.0
 27:          0          0          0          0   PCI-MSI 32771-edge      virtio0-input.1
 28:          0          0          0          0   PCI-MSI 32772-edge      virtio0-output.1
 29:          0          0          0          0   PCI-MSI 49152-edge      virtio1-config
 30:          1          0          0          0   PCI-MSI 49153-edge      virtio1-input.0
 31:          0          0          0          0   PCI-MSI 49154-edge      virtio1-output.0
 32:          0          0          0          0   PCI-MSI 49155-edge      virtio1-input.1
 33:          0          0          0          0   PCI-MSI 49156-edge      virtio1-output.1
```

## Split virtqueue / Packed virtqueue

参考

- [2020: Red Hat Blog: Virtio devices and drivers overview: The headjack and the phone](https://www.redhat.com/en/blog/virtio-devices-and-drivers-overview-headjack-and-phone)
- [2020: Red Hat Blog: Virtqueues and virtio ring: How the data travels](https://www.redhat.com/en/blog/virtqueues-and-virtio-ring-how-data-travels)
- [2020: Red Hat Blog: Packed virtqueue: How to reduce overhead with virtio](https://www.redhat.com/en/blog/packed-virtqueue-how-reduce-overhead-virtio)

1. Split Virtqueue（分割型）の課題：非効率なメモリ使用

- 従来の「Split Virtqueue」は設計がシンプルで優れていましたが、根本的な問題を抱えていました。
- メモリの分散: 「Descriptor Table」「Available Ring」「Used Ring」という 3 つのエリアがメモリ上の別々の場所に配置されています。
  - Descriptor Table: データ本体が置かれているアドレスとサイズのリスト。
  - Available Ring: ドライバーが「これを使って」とデバイスに指示するインデックスのリスト。
  - Used Ring: デバイスが「処理が終わったよ」と報告するインデックスのリスト。
- キャッシュへの負荷: データの読み書きの際、CPU がこれら離れたメモリ領域を何度も参照する必要があり、キャッシュ効率が低下します。
- ハードウェアへの影響: NIC などのハードウェア実装においては、1 つのデスクリプタ（記述子）を処理するために複数の PCI トランザクションが発生し、遅延の原因となっていました。

2. Packed Virtqueue（パケット型）による解決

- virtio 1.1 で導入された「Packed Virtqueue」は、「Descriptor Table」「Available Ring」「Used Ring」という 3 つのリングをゲストメモリ上の 1 つのリング（Descriptor Ring）に統合します。
- 考え方: デバイスがドライバーから読み取ったデータは上書きしてよいという性質を利用し、同じメモリ領域を循環させて利用します。
- フラグによる所有権管理（Wrap Counter 方式）
  - リングが統合されたことで「どの項目が未処理で、どれが処理済みか」を判別する必要があります。そこで導入されたのが**ラップカウンター（Wrap Counter）**です。
  - 仕組み: ドライバーとデバイスは、リストを一周するたびに反転する「1 ビットの変数（0 or 1）」を各自で持っています。
  - 所有権の判定: \* ドライバーはデータを置くとき、その項目の AVAIL フラグ を自分の現在のカウンター値に書き換えます。
    - デバイスは、その項目の AVAIL フラグ が自分のカウンター値と一致していれば「自分の番だ」と認識します。
    - 処理が終わると、デバイスは USED フラグ を更新してドライバーに返却します。
  - これにより、インデックスを管理する別個のリングを参照する必要がなくなり、**「リストの次の要素を見るだけ」**で処理が完結します。
- メリット
  - メモリの局所性（Locality）
    - データがメモリ上の 1 か所に固まっているため、CPU のプリフェッチ機能が効きやすくなり、キャッシュヒット率が劇的に向上します。
  - インオーダー（順序通り）処理の効率化
    - 多くのパケット処理では、データは投入した順番に処理されます。Packed Virtqueue はこの「順番通り」の処理に特化しており、複数の記述子をまとめてバッチ処理する際のオーバーヘッドが極めて小さくなっています。
  - ハードウェア・オフロードへの適性
    - スマート NIC（DPU）などのハードウェアで virtio を動かす場合、メモリへのアクセス回数を減らすことは消費電力の削減とスループットの向上に直結します。Packed Virtqueue はハードウェアが読み取るべきデータ量を最小限にするよう設計されています。

実際どうなの？

- パケットサイズ 64 バイトにおいて 約 15〜20% の性能向上が期待できる
  - 1500 バイトのような大きなパケットでは帯域幅（40Gbps/100Gbps）の上限に達してしまい、差が見えないことがあります。
  - Packed Virtqueue の真価は、CPU 負荷が高いショートパケット（64B）の大量転送時に現れます。
- データプレーンによる違い
  - vhost-net
    - カーネルの処理オーバーヘッドが大きいため、Virtqueue 自体の改善効果はあまりみられない?
  - DPDK(vhost-user)
    - [DPDK Performance Reports](https://fast.dpdk.org/doc/perf/)
      - パケットサイズが小さい(64B)場合、Packed Virtqueue の方が Split よりも 約 5% 〜 15% 高いスループット (Mpps) を記録する傾向があります。
  - ハードウェア (vDPA / SmartNIC)
    - PCI アクセスが激減するため、スループットとレイテンシの両方で劇的な向上が期待できる
