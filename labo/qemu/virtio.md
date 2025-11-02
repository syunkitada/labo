QEMU IO Thread

- 特定デバイス（ディスク）のエミュレーションを行うために、QEMU のメインスレッドとは別に生成した、ホスト側にある QEMU のスレッド。
- QEMU 内での非同期 IO 処理を QEMU のメインスレッドとは別のスレッドで行える
- libvirt のスキーマで明治 s 的にステイすると生成できる
- デフォルトでは、メインスレッドで IO 処理も行う

virtqueu

- virtio のキュー

virtqueue = vCPU 数の場合、書く vCPU ごとに virtqueu が割り当てられる

```
ls /sys/block/vda/mq/0/
```

virtqueue = 1 の場合は一つのキューを書く CPU が共有するお

qemu の I/O thread
あるバージョンまで、I/O thread は 1 に固定されていた

queue の確認方法
virsh qemu-monitor-command <uuid> --hmp "info virtio-queue-status /machine/peripheral/virtio-disk0/virtio-backend 0"

I/O Batch Submission: 複数の I/O Request を単一の I/O Request に束ねる機能

num-queue
iothreads
<cputune>
<iothreadpin iothread=1 cpuset=64 />

<qemu:commandline>
<qemu:arg value="">
</cputune>
