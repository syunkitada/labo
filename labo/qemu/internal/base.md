# 基礎

## QEMU

- Quick Emulator
- CPU、ディスク、NIC などのハードウェアをすべてエミュレートする仮想マシンエミュレータ
  - QEMU はすべてのハードウェアをエミュレート(完全仮想化)できるのが、これは処理が多くなり効率的ではない
  - そのため、CPU は kvm や仮想支援機構を利用して CPU 上で仮想マシンのコードを直接実行したり、ネットワーク処理はカーネルの機能に任せるなど、すべてを仮想化せずに一部エミュレートする(準仮想化)

## CPU のエミュレーション

- リングプロテクション
  - リングプロテクションとは、CPU の特権レベルのことで 0 ～ 3 まである。このレベルによって利用できる CPU の命令が異なる
  - ユーザプロセスはリング 3 で動き利用できる命令に制限があり、kernel はリング 0 で動き命令の制限がない
- センシティブ命令
  - CPU の命令には、計算だけでなく、IO などハードウェアを使う、センシティブ命令がある
  - 仮想マシンでセンシティブ命令が実行された場合、CPU はこれをフックして QEMU などのエミュレータがこれを適切にエミュレートする必要がある
- 仮想化支援機構と KVM
  - 従来の仮想マシンは、リング 3 で動いていた
    - 仮想マシンはあくまでユーザプロセスなので、リング 3 で動かす必要があった
    - そこで、OS を修正したり、VMM(仮想マシンモニタ)が命令を修正したりしてリング 3 で動くようにしていた
  - 仮想化支援機構(Intel VT-x AMD AMD-V)
    - CPU で仮想マシン用の実行モードをサポートすることで、仮想マシンのコードがリングプロテクションのもとで実行され、センシティブ命令時にはこれをトラップしてエミュレートできるようにした
    - CPU の実行モードには、通常のリングプロテクションの実行モード(VMX root モード)のほかに、仮想マシン実行用のモード(VMX nonroot モード)が追加された
    - 仮想マシンのコードが実行されるときは、CPU を VMX nonroot モードに切り替え(VM Enter)、CPU で仮想マシンのコードを直接実行する
      - 仮想マシンの kernel は VMX nonroot モードのリング 0 で実行され、ユーザプロセスは VMX nonroot モードのリング 3 で実行される
    - センシティブな命令が実行された場合には、いったん VMX root モードになって(VM Exit)、kvm がその制御を行う
      - kvm は、ネットワークなどの I/O 処理はカーネル空間上で処理が完結させるが、ディスク I/O などは kvm では扱えず、QEMU などのエミュレータに処理を依頼する
      - kvm が処理を完了すると、VMX nonroot モードに復帰して(VM Enter)、仮想マシンのコードが再び実行される
  - KVM
    - Kernel-based Virtual Machine
    - 仮想化支援機構を使って仮想マシン機能を提供するカーネルモジュール
- VM の実行時間(guest 時間)
  - ホスト側から mpstat を実行すると確認できる
    - QEMU がセンシティブ命令などをエミュレートしてる時間が user 時間
    - kernel(kvm など)の実行時間が sys 時間
    - VMX non-root モードで VM が実行してる時間が guest 時間
- VM の steal time
  - VM 側から mpstat を実行すると確認できる
  - VM がプロセスをスケジュールするとき、vcpu に CPU 時間を割り当てるが、実際にこれが実行されるのは、ホストが vcpu に実 CPU の時間を割り当てられる時である
  - このとき、実際に実行された cpu の時間と、VM が実行しようとした vcpu の時間の差分が、steal time となる
  - steal time は、vcpu の msr レジスタ経由で情報を kvm.ko から受け取り計算される
    - msr レジスタは、雑多な処理をするためのレジスタ

## KVM

- /dev/kvm
  - KVM のインターフェイスになる特殊デバイス
  - ioctl()で様々な機能を提供
- 仮想マシン作成の流れ
  - /dev/kvm で仮想マシンを作成すると、kvm-vm ファイル記述子が返される
  - kvm-vm を使って、メモリを割り当てる
  - kvm-vm を使って、vcpu をつくると、kvm-vcpu というファイル記述子が返され、1 つの vcpu ごとに vcpu スレッド作成して管理する
  - kvm-vcpu を使って、vcpu のレジスタ(pc など)に値をセットする
  - kvm-vcpu を使って、センシティブ命令(I/O)発生時のハンドラをセットする
  - kvm-vcpu を使って、vcpu をスタートする
  - keyboard 入力などの割り込みを発生させる場合は、kvm-vm を使って、kvm-vm が適切な vcpu に割り込みを入れる
    - ioctl(kvm-vm, KVM_IRQ_LINE_STATUS, 割り込み番号, {{irq=11, status=1}, ...)

```
$ sudo lsof -p 8988 | grep kvm
qemu-syst 8988 root   12u      CHR             10,232         0t0      425 /dev/kvm
qemu-syst 8988 root   13u  a_inode               0,11           0     7994 kvm-vm
qemu-syst 8988 root   18u  a_inode               0,11           0     7994 kvm-vcpu
qemu-syst 8988 root   19u  a_inode               0,11           0     7994 kvm-vcpu
```

## 仮想マシンのメモリ管理

- VM でも OS がページテーブルを管理しており、仮想アドレスを物理アドレスに変換している
- しかし、VM の物理アドレスというのは、QEMU で管理している仮想メモリ空間である実際のメモリアドレスとは異なるため、VM の物理アドレスをホストの物理アドレスに変換する仕組みが必要である
- シャドウページング
  - ホストはシャドウページテーブルという仮想アドレスと物理アドレスを変換できるページテーブルを作る
  - これと VM のページテーブルを同期させることで、VM からのメモリアクセスを可能にする
  - しかし、メモリの読み書きにいちいち同期をとる必要があるパフォーマンスがよくない
- EPT(Extended Page Table: Intel)、NPT(Nested Page Table: AMD)
  - EPT は MMU の拡張機能で、VM 物理アドレスをホスト物理アドレスに変換する機能をプロセッサレベルで提供する
    - EPT は VM 物理アドレス(GPA)からホスト物理アドレス(HPA)への変換を行う 4 段のページテーブル
    - 仕組みは通常のページテーブル機構とほぼ同じで、TLB も使うし、ページサイズが大きくなればページウォーク数も減る
  - まだテーブルにマッピングされていないアドレスへのアクセスが発生した場合 EPT Violation が発生し VMExit してページフォルトが発生する
  - VM 物理アドレスと物理アドレスをマッピングした情報は VMCS の EPTP(EPT Pointer)に登録しておき、MMU がこれを使って物理メモリにアクセスする
  - VM が仮想アドレスにアクセスすると、MMU がページテーブルにより VM 物理アドレスに変換し、MMU が EPT により物理アドレスに変換して物理アドレスに変換する
- THP の利用による高速化
  - ホストで THP を有効にしておくと、QEMU がページを確保する際に 2M のページサイズとなる
  - EPT でのページウォーク数も 4 から 3 になり、EPT での TLB ヒット率も上がり、ページテーブルのサイズも節約される
  - THP のデメリット
    - ページサイズを 2M にすると、ページフォルト時のページ初期化に時間がかかる
    - 仮想メモリのサイズが肥大化しやすい(実サイズは肥大化しないから問題ない?)
- Hugetlbfs による高速化
  - THP が 2M 固定なのに対して、2M もしくは 1G のページサイズを割り当てることができる
  - ページサイズを 1G にすれば、EPT でのページウォーク数も 4 から 2 になり、EPT での TLB ヒット率も上がり、ページテーブルサイズも節約される
  - THP との使い分け
    - Hugetlbfs は通常のメモリ空間とは隔離され、スワップアウトできず、ブート時に静的に確保しないといけない
    - 稼働させようとしている VM 数とそのメモリ利用量が見積れて、余裕があるなら Hugetlbfs を使うのが良い
    - そうでないなら、THP のほうがメモリの融通が利くので、THP のほうが良い
- 参考
  - [Red Hat: Transparent Hugepage Support](https://www.linux-kvm.org/images/9/9e/2010-forum-thp.pdf)
    - THP の説明、THP の有効/無効時、EPT 有効/無効時のベンチマークが乗ってる

## IO のエミュレーション

1. VM: VM のデバイスへの IO が実行される
2. VM: IO の実行にフックして VMExit が発生
3. ホスト: アクセス先のデバイス、アクセス幅、アクセス方向、書き込み先、読み込み元などを特定
4. ホスト: デバイス IO のエミュレーション処理を行う
5. ホスト: VMEnter してゲストを再開させる
6. VM: IO 実行の次の命令から実行再開

## eventfd

- パイプをデータを転送するのではなく、イベントの発生を通知するために使うことができる
- イベントの例
  - シグナルの受信
  - 非同期 IO の完了
- 送信側: 書き出し側のパイプ記述子経由で 1 バイトだけ書き出すことでイベントの発生を通知する
- 受信側: 読み込み側のパイプ記述子を read か poll/select して、待ち、書き込みがあると起床して 1 バイト読んで捨てる
- eventfd システムコール
  - パイプをイベントを通知するという目的に特化したファイルオブジェクトを作成するシステムコール
  - ファイルオブジェクトの中に 64bit の整数値(N)を一つ保持できる
  - EFS_SEMAPHORE を指定しなかった場合の動作
  - 通知側: write システムコールを呼び出すと N を増やす
  - 受信側: read システムコールを呼び出したとき N>0 だと N を一つ減らしてリターン、N == 0 だと wait キューにならび、N が増えるのを待つ
- qemu も

```
$ sudo lsof -p 8988 | grep eventfd
qemu-syst 8988 root    6u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root    8u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root    9u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   14u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   15u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   22u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   23u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   24u  a_inode               0,11          0     7994 [eventfd]
qemu-syst 8988 root   25u  a_inode               0,11          0     7994 [eventfd]
```

## virtio

- VM とホストで共有できるリングバッファを所持しており、ここに適切に情報を詰めることで、ゲストホスト間でデータを転送する
  - 例えば、コントロール用、TX 用、RX 用のリングバッファがあれば NIC みたいな動作もできる
- virtio は virt デバイスを提供しており、これが NIC、ブロックデバイスなどの IO 形の PCI デバイスとしてゲスト OS から認識され、virtio ドライバを介してアクセスされる
- I/O するデータが VM とホスト双方で共有で見えているので、データ受け渡しの際に vmexit、vmenter が不要になる
- evnetfd(irqfd, ioeventfd)を使って、vitio スレッドが割り込みや、イベント通知を受け取る
- VM には vitio ドライバが、NIC やディスクの IO デバイスのドライバとして扱われる
- irqfd
  - eventfd を使って、vmexit さずにホストから VM へ割り込みを行うための機構
    - eventfd の一端を kvm.ko とする
    - 割り込みの種類ごとの irqfd で割り込みを通知する
    - ホストが、write(irqfd, ...)で書き込み、vCPU が割り込まれる
- ioeventfd

  - eventfd を使って、vmexit せずにゲストから Output 命令を受信するための機構
  - IO 先ごとの ioeventfd でセンシティブ命令の実行を通知する
  - vmexit しない

- 参考
  - [KVM irqfd and ioeventfd](http://blog.allenx.org/2015/07/05/kvm-irqfd-and-ioeventfd)
  - [irqfd patch](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=721eecbf4fe995ca94a9edec0c9843b1cc0eaaf3)
  - [ioeventfd](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d34e6b175e61821026893ec5298cc8e7558df43a)

```
$ lspci
00:00.0 Host bridge: Intel Corporation 440FX - 82441FX PMC [Natoma] (rev 02)
00:01.0 ISA bridge: Intel Corporation 82371SB PIIX3 ISA [Natoma/Triton II]
00:01.1 IDE interface: Intel Corporation 82371SB PIIX3 IDE [Natoma/Triton II]
00:01.2 USB controller: Intel Corporation 82371SB PIIX3 USB [Natoma/Triton II] (rev 01)
00:01.3 Bridge: Intel Corporation 82371AB/EB/MB PIIX4 ACPI (rev 03)
00:02.0 Ethernet controller: Red Hat, Inc Virtio network device
00:03.0 Unclassified device [00ff]: Red Hat, Inc Virtio memory balloon


$ cat /proc/interrupts  | grep virtio
 11:          1          0   IO-APIC-fasteoi   uhci_hcd:usb1, virtio1
 24:          0          0   PCI-MSI-edge      virtio0-config
 25:         19       4690   PCI-MSI-edge      virtio0-input.0
 26:          1          0   PCI-MSI-edge      virtio0-output.0
```

ゲストがホストにデータを転送してほしい場合、
ゲストは IO ポートを使ってエミュレータ(vitio server)をキック
ホスト リングバッファにデータを入れる
ホストがゲストの割り込みハンドラ(IRQ、MSI-X)をキック

## ネットワーク IO のエミュレーション

- vhost-net
  - 昔は、ネットワークデバイスも virtio-server を用いてパケットの入出力を行っていた
  - しかし、virtio-server を通してパケット処理するのは無駄なので(ユーザ空間の処理が入る)、カーネルの vhost-net モジュールによってホスト・ゲストのパケット入出力を制御するようになった
  - NIC ドライバ -> bridge -> tap ドライバ -> vhost-net -> kvm -> 割り込み -> virtio ドライバ -> VM のネットワークスタック
  - zero copy
    -
- LinuxBridge
  - Linux に標準でついてるブリッジ
  - 機能自体はただの L2 で動作するソフトウェアブリッジ
- OpenvSwitch
  - openflow に準拠したブリッジ
  - L2 のブリッジ機能に加え、フロー制御や QOS 制御ができる
- PCI パススルー
  - PCI デバイスをゲスト OS に直接見せて利用する
- SR-IOV
  - NIC が仮想 NIC(VF: Virtual Function)を提供し、これをゲスト OS に直接見せて利用する
- DPDK+OVS
  - vhost-net と ovs が linux socket(vhost-net=client, ovs=server)でつながるため、ovs が落ちると vhost-net はつなぎなおしてくれない
    - 2.6 系以上で導入された ovs=client モードにすると、ovs がつなぎなおせるようになる
  - 処理フロー
    - NIC にパケットが到着(リングバッファに保存)
    - NIC がメモリにパケットを書き込む(ハードウェア割り込みは入らない)
    - PMD(Poll Mode Driver)がメモリを定期的に取得し、パケットを DPDK を介して参照渡しする
    - OVS がパケットをルーティングし、宛先の VM の vhost-user に私、vcpu に割り込む
    - VM もネットワークスタック

## 参考

- https://lwn.net/Articles/658511/
- [Linux KVM のコードを追いかけてみよう] (http://www.slideshare.net/ozax86/linux-kvm?qid=fb99f565-8ae4-44d3-9b58-8d8487197566&v=&b=&from_search=26)
- [ハイパーバイザの作り方](http://syuu1228.github.io/howto_implement_hypervisor/)
- [KVM の中身](http://rkx1209.hatenablog.com/entry/2016/01/01/101456)
- [Asynchronous page fault 解析](http://d.hatena.ne.jp/kvm/20110702/1309604602)
