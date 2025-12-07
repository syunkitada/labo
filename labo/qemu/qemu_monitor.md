# QEMU Monitor Commands

```
$ virsh qemu-monitor-command 1 --hmp "info cpus"
* CPU #0: thread_id=218777
  CPU #1: thread_id=218778
  CPU #2: thread_id=218779
  CPU #3: thread_id=218780
```

```
$ virsh qemu-monitor-command 1 --hmp "info blockstats"
: rd_bytes=224383488 wr_bytes=14574592 rd_operations=7925 wr_operations=436 flush_operations=50 wr_total_time_ns=2573844594 rd_total_time_ns=18676133881 flush_total_time_ns=204483001 rd_merged=17 wr_merged=8 idle_time_ns=34086279798
: rd_bytes=174294 wr_bytes=0 rd_operations=55 wr_operations=0 flush_operations=0 wr_total_time_ns=0 rd_total_time_ns=250426651 flush_total_time_ns=0 rd_merged=0 wr_merged=0 idle_time_ns=273191352356

$ virsh qemu-monitor-command 1 --hmp "info block -v"
libvirt-2-format: /mnt/sda/exports/mylabo/vms/VM1.rocky9.mylabo.test/img (qcow2)
    Attached to:      /machine/peripheral/virtio-disk0/virtio-backend
    Cache mode:       writeback, direct

Images:
image: /mnt/sda/exports/mylabo/vms/VM1.rocky9.mylabo.test/img
file format: qcow2
virtual size: 40 GiB (42949672960 bytes)
disk size: 1.45 GiB
cluster_size: 65536
Format specific information:
    compat: 1.1
    compression type: zlib
    lazy refcounts: false
    refcount bits: 16
    corrupt: false
    extended l2: false

libvirt-1-format: /mnt/sda/exports/mylabo/vms/VM1.rocky9.mylabo.test/config.img (raw, read-only)
    Attached to:      ide0-0-0
    Removable device: locked, tray closed
    Cache mode:       writeback, direct

Images:
image: /mnt/sda/exports/mylabo/vms/VM1.rocky9.mylabo.test/config.img
file format: raw
virtual size: 366 KiB (374784 bytes)
disk size: 368 KiB
```

```
info trace-events [name] [vcpu]
```

```
info sev  -- show SEV information
```

```
$ virsh qemu-monitor-command 1 --hmp "info roms"
fw=genroms/kvmvapic.bin size=0x002400 name="kvmvapic.bin"
addr=00000000fffc0000 size=0x040000 mem=rom name="bios-256k.bin"
```

```
$ virsh qemu-monitor-command 1 --hmp "info numa"
0 nodes
```

```
$ virsh qemu-monitor-command 1 --hmp "info network"
net0: index=0,type=nic,model=virtio-net-pci,macaddr=00:16:3e:00:00:01
 \ hostnet0: index=0,type=tap,fd=34
net0: index=1,type=nic,
 \ hostnet0: index=1,type=tap,fd=36
net0: index=2,type=nic,
 \ hostnet0: index=2,type=tap,fd=37
net0: index=3,type=nic,
 \ hostnet0: index=3,type=tap,fd=38
net0: index=4,type=nic,
 \ hostnet0: index=4,type=tap,fd=39
```

```
$ virsh qemu-monitor-command 1 '{"execute":"query-blockstats"}' | jq .
 ...
```

```
$ virsh qemu-monitor-command 3 --hmp "info virtio"
/machine/peripheral/balloon0/virtio-backend [virtio-balloon]
/machine/peripheral/virtio-disk0/virtio-backend [virtio-blk]
/machine/peripheral/net0/virtio-backend [virtio-net]
```

```
$ virsh qemu-monitor-command 3 --hmp "info virtio-queue-status /machine/peripheral/virtio-disk0/virtio-backend 0"
/machine/peripheral/virtio-disk0/virtio-backend:
  device_name:          virtio-blk
  queue_index:          0
  inuse:                0
  used_idx:             1558
  signalled_used:       1558
  signalled_used_valid: true
  last_avail_idx:       1558
  shadow_avail_idx:     1558
  VRing:
    num:          256
    num_default:  256
    align:        4096
    desc:         0x000000010b89c000
    avail:        0x000000010b89d000
    used:         0x000000010b89d240

$ virsh qemu-monitor-command 3 --hmp "info virtio-status /machine/peripheral/virtio-disk0/virtio-backend"
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
  num_vqs:                 4
  queue_sel:               3
  isr:                     1
  endianness:              little
  status:
  ...
```
