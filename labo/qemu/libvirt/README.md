# Libvirt

## domxml-to-native

```
$ sudo virsh dumpxml VM1.mylabo.test > /tmp/domain.xml

$ virsh domxml-to-native qemu-argv /tmp/domain.xml
LC_ALL=C PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin HOME=/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test XDG_DATA_HOME=/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test/.local/share XDG_CACHE_HOME=/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test/.cache XDG_CONFIG_HOME=/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test/.config /usr/bin/qemu-system-x86_64 -name guest=VM1.mylabo.test,debug-threads=on -object '{"qom-type":"secret","id":"masterKey0","format":"raw","file":"/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test/master-key.aes"}' -machine pc-i440fx-jammy,usb=off,dump-guest-core=off,memory-backend=pc.ram -accel kvm -cpu qemu64 -m 4096 -object '{"qom-type":"memory-backend-ram","id":"pc.ram","size":4294967296}' -overcommit mem-lock=off -smp 4,sockets=4,cores=1,threads=1 -uuid 01f43336-36eb-4806-a67e-701aac32e38b -no-user-config -nodefaults -chardev socket,id=charmonitor,path=/var/lib/libvirt/qemu/domain--1-VM1.mylabo.test/monitor.sock,server=on,wait=off -mon chardev=charmonitor,id=monitor,mode=control -rtc base=utc -no-shutdown -no-acpi -boot strict=on -device piix3-usb-uhci,id=usb,bus=pci.0,addr=0x1.0x2 -blockdev '{"driver":"file","filename":"/mnt/sda/exports/mylabo/vms/VM1.mylabo.test/img","node-name":"libvirt-1-storage","auto-read-only":true,"discard":"unmap"}' -blockdev '{"node-name":"libvirt-1-format","read-only":false,"driver":"raw","file":"libvirt-1-storage"}' -device virtio-blk-pci,bus=pci.0,addr=0x4,drive=libvirt-1-format,id=virtio-disk0,bootindex=1 -netdev tap,fd=25,id=hostnet0 -device rtl8139,netdev=hostnet0,id=net0,mac=00:16:3e:00:00:01,bus=pci.0,addr=0x3 -audiodev '{"id":"audio1","driver":"none"}' -vnc 127.0.0.1:0,audiodev=audio1 -k de -device cirrus-vga,id=video0,bus=pci.0,addr=0x2 -device virtio-balloon-pci,id=balloon0,bus=pci.0,addr=0x5 -sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny -msg timestamp=on
```

## Pass-through of arbitrary qemu commands

https://libvirt.org/drvqemu.html#pass-through-of-arbitrary-qemu-commands

```
<domain type='qemu' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
....snip.....
  <qemu:commandline>
    <qemu:arg value='-newarg'/>
    <qemu:env name='QEMU_ENV' value='VAL'/>
  </qemu:commandline>
</domain>
```
