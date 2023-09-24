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
