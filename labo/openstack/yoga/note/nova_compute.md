# nova-compute

## サービスの起動

```cmd/compute.py
44 def main():
45     config.parse_args(sys.argv)
46     logging.setup(CONF, 'nova')
47     priv_context.init(root_helper=shlex.split(utils.get_root_helper()))
48     objects.register_all()
49     gmr_opts.set_defaults(CONF)
50     # Ensure os-vif objects are registered and plugins loaded
51     os_vif.initialize()
52
53     gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)
54
55     # disable database access for this service
56     nova.db.main.api.DISABLE_DB_ACCESS = True
57     objects_base.NovaObject.indirection_api = conductor_rpcapi.ConductorAPI()
58     objects.Service.enable_min_version_cache()     ■ "Service" is not a known member of module "nova.objects"
59     server = service.Service.create(binary='nova-compute',
60                                     topic=compute_rpcapi.RPC_TOPIC)
61     service.serve(server)
62     service.wait()
```

- objects_base.NovaObject.indirection_api = conductor_rpcapi.ConductorAPI()
  - indirection_api をセットしてると、一部の Object の save 時に nova-conductor の RPC 経由で DB に save します

## service 状態の定期レポート

- CONF.report_interval の間隔で、nova-conductor の RPC 経由で service オブジェクトを保存します

```python:servicegroup/drivers/db.py
32 class DbDriver(base.Driver):
33
34     def __init__(self, *args, **kwargs):
35         self.service_down_time = CONF.service_down_time
36
37     def join(self, member, group, service=None):
38         """Add a new member to a service group.
39
40         :param member: the joined member ID/name
41         :param group: the group ID/name, of the joined member
42         :param service: a `nova.service.Service` object
43         """
44         LOG.debug('DB_Driver: join new ServiceGroup member %(member)s to '
45                   'the %(group)s group, service = %(service)s',
46                   {'member': member, 'group': group,
47                    'service': service})
48         if service is None:
49             raise RuntimeError(_('service is a mandatory argument for DB based'
50                                  ' ServiceGroup driver'))
51         report_interval = service.report_interval
52         if report_interval:
53             service.tg.add_timer_args(
54                 report_interval, self._report_state, args=[service],
55                 initial_delay=api.INITIAL_REPORTING_DELAY)
...
87     def _report_state(self, service):
88         """Update the state of this service in the datastore."""
89
90         try:
91             service.service_ref.report_count += 1
92             service.service_ref.save()
```

- service.service_ref.save()
  - service_ref は objects.Service のインスタンスです。
  - objects.Service の save には@base.remotable デコレータがついています。
  - remotable は、objects.Service の indirection_api がセットされてる場合はこれを利用します。
  - nova-compute は、起動時に objects_base.NovaObject.indirection_api = conductor_rpcapi.ConductorAPI() としています。
  - これにより、RPC 経由で nova-conductor が service を更新します。

```objects/service.py
228 @base.NovaObjectRegistry.register
229 class Service(base.NovaPersistentObject, base.NovaObject, base.NovaObjectDictCompat):     ■ line too long (85 > 79 characters)
...
465     @base.remotable
466     def save(self):
...
```

```objects/base.py
25 from oslo_versionedobjects import base as ovoo_base
...
94 remotable = ovoo_base.remotable
```

```oslo_versionedobjects/base.py
195 # See comment above for remotable_classmethod()
196 #
197 # Note that this will use either the provided context, or the one
198 # stashed in the object. If neither are present, the object is
199 # "orphaned" and remotable methods cannot be called.
200 def remotable(fn):
201     """Decorator for remotable object methods."""
202     @functools.wraps(fn)
203     def wrapper(self, *args, **kwargs):
204         ctxt = self._context
205         if ctxt is None:
206             raise exception.OrphanedObjectError(method=fn.__name__,
207                                                 objtype=self.obj_name())
208         if self.indirection_api:
209             updates, result = self.indirection_api.object_action(
210                 ctxt, self, fn.__name__, args, kwargs)
211             for key, value in updates.items():
212                 if key in self.fields:
213                     field = self.fields[key]
214                     # NOTE(ndipanov): Since VersionedObjectSerializer will have
215                     # deserialized any object fields into objects already,
216                     # we do not try to deserialize them again here.
217                     if isinstance(value, VersionedObject):
218                         setattr(self, key, value)
219                     else:
220                         setattr(self, key,
221                                 field.from_primitive(self, key, value))
222             self.obj_reset_changes()
223             self._changed_fields = set(updates.get('obj_what_changed', []))
224             return result
225         else:
226             return fn(self, *args, **kwargs)
227
228     wrapper.remotable = True
229     wrapper.original_fn = fn
230     return wrapper
```

nova-compute の RPC 呼び出し時のスタックトレースは以下になります。

```
/opt/nova/lib/python3.10/site-packages/eventlet/greenthread.py(221)main()
-> result = function(*args, **kwargs)
  /opt/nova/lib/python3.10/site-packages/oslo_service/loopingcall.py(150)_run_loop()
-> result = func(*self.args, **self.kw)
  /opt/nova/lib/python3.10/site-packages/nova/servicegroup/drivers/db.py(92)_report_state()
-> service.service_ref.save()
  /opt/nova/lib/python3.10/site-packages/oslo_versionedobjects/base.py(209)wrapper()
-> updates, result = self.indirection_api.object_action(
  /opt/nova/lib/python3.10/site-packages/nova/conductor/rpcapi.py(247)object_action()
-> return cctxt.call(context, 'object_action', objinst=objinst,
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/client.py(190)call()
-> result = self.transport._send(
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/transport.py(123)_send()
-> return self._driver.send(target, ctxt, message,
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/_drivers/amqpdriver.py(795)send()
-> return self._send(
> /opt/nova/lib/python3.10/site-packages/oslo_messaging/_drivers/amqpdriver.py(686)_send()
```

RPC で送信する message は以下のようになっています。  
methond に object_action、args として、objinst にオブジェクトのデータ、objmethod に save が指定されています。

```
_send {'method': 'object_action', 'args': {'objinst': {'nova_object.name': 'Service', 'nova_object.namespace': 'nova', 'nova_object.version': '1.22', 'nova_object.data': {'id': 12, 'uuid': '9f6b3edf-4dff-4124-adff-3ba10080c799', 'host': '904c4d30b165', 'binary': 'nova-compute', 'topic': 'compute', 'report_count': 3684, 'disabled': False, 'disabled_reason': None, 'last_seen_up': '2023-10-22T10:45:31Z', 'forced_down': False, 'version': 61, 'created_at': '2023-10-09T08:21:32Z', 'updated_at': '2023-10-22T10:45:31Z', 'deleted_at': None, 'deleted': False}, 'nova_object.changes': ['report_count']}, 'objmethod': 'save', 'args': (), 'kwargs': {}}, 'version': '3.0'}
```

nova-conductor は、object_action を実行し、objinst に指定されたデータ(service)の objmethod(save)を実行し、DB に保存します。

```
/opt/nova/lib/python3.10/site-packages/eventlet/greenpool.py(88)_spawn_n_impl()
-> func(*args, **kwargs)
  /opt/nova/lib/python3.10/site-packages/futurist/_green.py(69)__call__()
-> self.work.run()
  /opt/nova/lib/python3.10/site-packages/futurist/_utils.py(45)run()
-> result = self.fn(*self.args, **self.kwargs)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/server.py(163)_process_incoming()
-> res = self.dispatcher.dispatch(message)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py(309)dispatch()
-> return self._do_dispatch(endpoint, method, ctxt, args)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py(229)_do_dispatch()
-> result = func(ctxt, **new_args)
  /opt/nova/lib/python3.10/site-packages/nova/conductor/manager.py(172)object_action()
-> result = self._object_dispatch(objinst, objmethod, args, kwargs)
  /opt/nova/lib/python3.10/site-packages/nova/conductor/manager.py(140)_object_dispatch()
-> return getattr(target, method)(*args, **kwargs)
  /opt/nova/lib/python3.10/site-packages/oslo_versionedobjects/base.py(226)wrapper()
-> return fn(self, *args, **kwargs)
> /opt/nova/lib/python3.10/site-packages/nova/objects/service.py(470)save()
-> updates = self.obj_get_changes()
```

## periodic_task

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _check_instance_build_time(self, context):
```

- \_check_instance_build_time
  - DB アクセスして、vm_state=vm_states.BUILDING の VM 一覧を取得
  - CONF.instance_build_timeout を経過してるかをチェックし、timeout した場合は、DB アクセスして VM を ERROR に更新する

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.scheduler_instance_sync_interval)
./compute/manager.py-    def _sync_scheduler_instance_info(self, context):
```

- \_sync_scheduler_instance_info
  - scheduler に instance_info をレポートします
  - 各 scheduler は HostManager の instance_info と呼ばれるホストごとのインスタンス情報の dict を持っておりこれを更新します
  - DB へのアクセスはなく、scheduler プロセスのオンメモリデータの更新するだけです

```
./compute/manager.py:    @periodic_task.periodic_task(
./compute/manager.py-        spacing=CONF.heal_instance_info_cache_interval)
./compute/manager.py-    def _heal_instance_info_cache(self, context):
```

- \_heal_instance_info_cache
  - この host 上の instance(BUILDING でも DELETING でもないもの)の uuids のキャッシュを維持します
  - DB アクセスして instance 一覧を取得し一つだけ pop して、network api を呼び出します
    - self.network_api.get_instance_nw_info を実行し、neutron の get_ports を呼び出します
    - これを実施しないと、metadata サービスが network の情報を追従できなくなる?
  - 必要に応じて、evacuation が fail した場合の network 情報の修正も行います

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _poll_rebooting_instances():
```

- \_poll_rebooting_instances
  - CONF.reboot_timeout が 0 より大きい場合に有効（デフォルト値は 0 で無効）
  - DB アクセスして REBOOTING, REBOOT_STARTED, REBOOT_PENDING の instance 一覧を取得する
  - CONF.reboot_timeout が経過してない場合は、self.driver.poll_rebooting_instances を実行します
  - ちなみに libvirt driver では何もしないので、libvirt を使う場合は意味がありません

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _poll_rescued_instances(self, context):
```

- \_poll_rescued_instances
  - CONF.rescue_timeout が 0 より大きい場合に有効（デフォルト値は 0 で無効）
  - DB アクセスして RESCUED の instance 一覧を取得してる
  - CONF.rescue_timeout が経過した instance を、nova-api を叩いて unrescue します

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _poll_unconfirmed_resizes(self, context):
```

- \_poll_unconfirmed_resizes
  - CONF.resize_confirm_window が 0 出ない場合に有効（デフォルト値は 0 で無効）
  - DB アクセスして resize_confirm_window の時間が経過した confirm されてない instance 一覧を取得する
  - instance を confirm_resize します

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.shelved_poll_interval)
./compute/manager.py-    def _poll_shelved_instances(self, context):
```

- \_poll_shelved_instances
  - CONF.shelved_offload_time が 0 よりも大きい場合に有効（デフォルト値は 0 で無効）
  - DB アクセスして SHELVED の instance 一覧を取得する
  - shelved_offload_time が経過した instance を削除します
    - shelved_offload_time が 0 の場合は、shelve 操作のときにそのまま削除します

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _instance_usage_audit(self, context):
```

- \_instance_usage_audit
  - CONF.instance_usage_audit が True の場合に有効（デフォルト値は False で無効）
  - Telemetry サービスで利用される nitify を送ります

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.volume_usage_poll_interval)
./compute/manager.py-    def _poll_volume_usage(self, context):
```

- \_poll_volume_usage
  - CONF.volume_usage_poll_interval が 0 でない場合に有効（デフォルト値は 0 で無効）
  - volume_usage_cache を更新するための notify を送ります

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.sync_power_state_interval,
./compute/manager.py-                                 run_immediately=True)
./compute/manager.py-    def _sync_power_states(self, context):
```

- \_sync_power_states
  - DB アクセスして HV 上の instance 一覧を取得し、driver からも instance の一覧を取得して instance の power_state を同期します
  - power_state が不一致の場合は、VM の実際の状態に合わせて、DB の power_state を更新します
  - vm_state が STOPPED なのに、VM が起動している場合は、VM を停止させます

```
./compute/manager.py:    @periodic_task.periodic_task
./compute/manager.py-    def _reclaim_queued_deletes(self, context):
```

- \_reclaim_queued_deletes
  - CONF.reclaim_instance_interval が 0 よりも大きい場合に有効（デフォルト値は 0 で無効）
  - instance を削除する際に、reclaim_instance_interval が 0 の場合はすぐに削除されます
  - reclaim_instance_interval が 0 よりも大きい場合は、この値が経過した場合にこのタスクによって削除されます

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.update_resources_interval)
./compute/manager.py-    def update_available_resource(self, context, startup=False):
```

- update_available_resource
  - DB にアクセスして自 Node の情報を取得します
  - DB の情報と自 Node の情報に差分がある場合は、DB アクセスして情報を更新します
  - placement に compute 情報をレポートします

```
./compute/manager.py:    @periodic_task.periodic_task(
./compute/manager.py-        spacing=CONF.running_deleted_instance_poll_interval,
./compute/manager.py-        run_immediately=True)
./compute/manager.py-    def _cleanup_running_deleted_instances(self, context):
```

- \_cleanup_running_deleted_instances
  - CONF.running_deleted_instance_action(デフォルト値は reap)に応じて、VM が稼働してしまっている削除済みの instance に対するアクションを実施します
  - reap の場合は、VM を停止してリソースを削除します

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.image_cache.manager_interval,
./compute/manager.py-                                 external_process_ok=True)
./compute/manager.py-    def _run_image_cache_manager_pass(self, context):
```

- \_run_image_cache_manager_pass
  - driver が、has_imagecache をサポートしてる場合に有効
  - DB アクセスして instance 一覧を取得し、driver の image_cache_manager を更新します

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.instance_delete_interval)
./compute/manager.py-    def _run_pending_deletes(self, context):
```

- \_run_pending_deletes
  - instance_delete_interval のデフォルト値は 300
  - 失敗した instance 削除を再試行するタスクです
  - DB アクセスして削除済みで cleaned が False の instance 一覧を取得します
  - ファイルを削除できたら、DB アクセスして cleaned を True にして更新します

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.instance_delete_interval)
./compute/manager.py-    def _cleanup_incomplete_migrations(self, context):
```

- \_cleanup_incomplete_migrations
  - DB アクセスして、status=error のマイグレーション一覧を取得します
  - DB アクセスして、マイグレーション一覧のインスタンスのうち削除済みのインスタンス一覧を取得します
  - そのインスタンスの関連ファイルを削除して、DB アクセスしてマイグレーション情報を更新します

```
./compute/manager.py:    @periodic_task.periodic_task(spacing=CONF.instance_delete_interval)
./compute/manager.py-    def _cleanup_expired_console_auth_tokens(self, context):
```

- \_cleanup_expired_console_auth_tokens
  - DB アクセスして、expired な console_auth_token を削除します
