# Disk IO

- Disk IO は、通常QEMU のメインスレッドで処理される
- 大量の IO リクエストが発生する場合、メインスレッドでの IO 処理がボトルネックになる可能性がある
- この問題を解決するために、QEMU は IO Thread 機能を提供している
- IO Thread を使用すると、特定のデバイス（ディスク）のエミュレーションを行うために、QEMU のメインスレッドとは別にスレッドを生成できる
- これにより、QEMU 内での非同期 IO 処理を QEMU のメインスレッドとは別のスレッドで行うことができ、IO 処理のパフォーマンスが向上する

## Virtio のキュー

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

## I/O Batch Submission

- 複数の I/O Request を単一の I/O Request に束ねる機能
