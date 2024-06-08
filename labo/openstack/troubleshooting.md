# troubleshooting

## keystone

```
# keystoneのdb_syncで以下のエラー
$ /opt/keystone/bin/keystone-manage --config-dir /etc/keystone/keystone.conf db_sync
Exception ignored in: <function _removeHandlerRef at 0x7fdc11bd41f0>
Traceback (most recent call last):
  File "/usr/lib/python3.10/logging/__init__.py", line 846, in _removeHandlerRef
  File "/usr/lib/python3.10/logging/__init__.py", line 226, in _acquireLock
  File "/usr/lib/python3.10/threading.py", line 164, in acquire
  File "/usr/lib/python3/dist-packages/eventlet/green/thread.py", line 33, in get_ident
AttributeError: 'NoneType' object has no attribute 'getcurrent'

# logっぽかったので、oslo.logのバージョンを下げたらでなくなった
$ /opt/keystone/bin/pip install 'oslo.log<5.3.0'
```

## neutron

neutron 起動直後に openstack port list をすると以下のエラーが出る。

```
root@3864d5063faa:/# openstack port list
HttpException: 500: Server Error for url: http://localhost:9696/v2.0/ports?fields=id&fields=name&fields=mac_address&fields=fixed_ips&fields=status, Request Failed: internal server error while processing your request.
```

```
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation [None req-104a5756-d0b3-4d08-aadf-7e82ad766531 0beb0849c44d4fd6866f2f2d546bcd33 21a67183fc7e4f0fb1751c7de5ffddb5 - - default default] GET failed.: AttributeError: type object 'Port' has no attribute 'port_forwardings'
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation Traceback (most recent call last):
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/pecan/core.py", line 682, in __call__
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     self.invoke_controller(controller, args, kwargs, state)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/pecan/core.py", line 573, in invoke_controller
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     result = controller(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron_lib/db/api.py", line 137, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     with excutils.save_and_reraise_exception():
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 227, in __exit__
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     self.force_reraise()
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 200, in force_reraise
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     raise self.value
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron_lib/db/api.py", line 135, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return f(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_db/api.py", line 144, in wrapper
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     with excutils.save_and_reraise_exception() as ectxt:
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 227, in __exit__
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     self.force_reraise()
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 200, in force_reraise
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     raise self.value
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_db/api.py", line 142, in wrapper
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return f(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron_lib/db/api.py", line 181, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     with excutils.save_and_reraise_exception():
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 227, in __exit__
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     self.force_reraise()
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/oslo_utils/excutils.py", line 200, in force_reraise
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     raise self.value
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron_lib/db/api.py", line 179, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return f(*dup_args, **dup_kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron/pecan_wsgi/controllers/utils.py", line 65, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return f(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron/pecan_wsgi/controllers/resource.py", line 135, in index
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return self.get(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron/pecan_wsgi/controllers/resource.py", line 144, in get
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return {self.collection: self.plugin_lister(*lister_args,
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron_lib/db/api.py", line 218, in wrapped
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     return method(*args, **kwargs)
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation   File "/opt/neutron/lib/python3.10/site-packages/neutron/db/db_base_plugin_v2.py", line 1608, in get_ports
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation     lazy_fields = [models_v2.Port.port_forwardings,
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation AttributeError: type object 'Port' has no attribute 'port_forwardings'
2023-10-01 19:17:36.621 183924 ERROR neutron.pecan_wsgi.hooks.translation
```

以下のバグ報告で説明されているが、以下のように api_workers を 1 にして network list を実行することで回避できた。
ワークアラウンドとして回避はできそうだが、これでよいのか、、。
https://bugs.launchpad.net/neutron/+bug/2028285

```
root@3864d5063faa:/# openstack port list
HttpException: 500: Server Error for url: http://localhost:9696/v2.0/ports?fields=id&fields=name&fields=mac_address&fields=fixed_ips&fields=status, Request Failed: internal server error while processing your request.

# neutron.confのworkerを1にしてrestartする
root@3864d5063faa:/# vim /etc/neutron/neutron.conf
api_workers = 1
root@3864d5063faa:/# systemctl restart neutron-server

root@3864d5063faa:/# openstack network list
+--------------------------------------+----------+--------------------------------------+
| ID                                   | Name     | Subnets                              |
+--------------------------------------+----------+--------------------------------------+
| 637e0aca-d23b-46d8-90e1-0e0643ea70d5 | localnet | b85af617-a2e1-49c7-a277-1e26cf0329a5 |
+--------------------------------------+----------+--------------------------------------+

root@3864d5063faa:/# openstack port list
```

メモ

- models_v2.Port には port_forwardings は定義されていないが、network list などを実行することで、models_v2.Port に port_forwardings が付与される
- worker ごとに model も別、、

## libvirt on docker with AppArmor

Ubuntuにおいて、docker上でlibvirtを動かすには、AppArmorの設定を変更する必要がある

```
$ virsh version
Compiled against library: libvirt 9.5.0
Using library: libvirt 9.5.0
Using API: QEMU 9.5.0
error: failed to get the hypervisor version
error: internal error: Cannot find suitable emulator for x86_64
```

## Failed to start QEMU binary /usr/libexec/qemu-kvm for probing: libvirt: error : cannot execute binary /usr/libexec/qemu-kvm: Permission denied

参考: https://github.com/kubevirt/kubevirt/issues/4303#issuecomment-715564964

```
internal error: Failed to start QEMU binary /usr/libexec/qemu-kvm for probing: libvirt:  error : cannot execute binary /usr/libexec/qemu-kvm: Permission denied
```

```
   /usr/{lib,lib64,lib/qemu,libexec}/vhost-user-gpu PUx,
   /usr/{lib,lib64,lib/qemu,libexec}/virtiofsd PUx,
>  /usr/libexec/qemu-kvm PUx,
```

## Cannot delete directory '/run/libvirt/xxx'

```
2024-03-17 13:45:10.711 1 ERROR nova.compute.manager [instance: 87799560-117e-400c-9a25-b70cc0f29e73]     raise libvirtError('virDomainCreateWithFlags() failed')
2024-03-17 13:45:10.711 1 ERROR nova.compute.manager [instance: 87799560-117e-400c-9a25-b70cc0f29e73] libvirt.libvirtError: internal error: Process exited prior to exec: libvirt:  error : Cannot delete directory '/run/libvirt/qemu/2-instance-00000002.shm': Device or resource busy
2024-03-17 13:45:10.711 1 ERROR nova.compute.manager [instance: 87799560-117e-400c-9a25-b70cc0f29e73]
```

```
2024-03-17 13:50:15.901 1 ERROR nova.compute.manager [instance: e24fc053-15c2-4f1a-a91c-8c9f58427720]     raise libvirtError('virDomainCreateWithFlags() failed')
2024-03-17 13:50:15.901 1 ERROR nova.compute.manager [instance: e24fc053-15c2-4f1a-a91c-8c9f58427720] libvirt.libvirtError: internal error: Process exited prior to exec: libvirt: QEMU Driver error : failed to umount devfs on /dev: Permission denied
```

参考: https://mattventura.net/2023/06/21/quick-fix-apparmorlibvirt-errors-in-debian-round-2/

```
   mount options=(rw,rslave)  -> /,
   mount options=(rw, nosuid) -> /{var/,}run/libvirt/qemu/*.dev/,
   umount /{var/,}run/libvirt/qemu/*.dev/,
>  umount /{var/,}run/libvirt/qemu/**,
>  umount /dev/,
```
