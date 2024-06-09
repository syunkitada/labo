# nova-scheduler

## サービスの起動

```python
/opt/nova/lib/python3.10/site-packages/nova/cmd/scheduler.py
38 def main():
39     config.parse_args(sys.argv)
40     logging.setup(CONF, "nova")
41     objects.register_all()
42     gmr_opts.set_defaults(CONF)
43     objects.Service.enable_min_version_cache()
44
45     gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)
46
47     server = service.Service.create(
48         binary='nova-scheduler', topic=rpcapi.RPC_TOPIC)
49
50     # Determine the number of workers; if not specified in config, default
51     # to number of CPUs
52     workers = CONF.scheduler.workers or processutils.get_worker_count()
53     service.serve(server, workers=workers)
54     service.wait()
```

```
/opt/nova/lib/python3.10/site-packages/oslo_service/service.py
(Pdb) where
  /opt/nova/bin/nova-scheduler(10)<module>()
-> sys.exit(main())
  /opt/nova/lib/python3.10/site-packages/nova/cmd/scheduler.py(53)main()
-> service.serve(server, workers=workers)
  /opt/nova/lib/python3.10/site-packages/nova/service.py(487)serve()
-> _launcher = service.launch(CONF, server, workers=workers,
  /opt/nova/lib/python3.10/site-packages/oslo_service/service.py(832)launch()
-> launcher = ServiceLauncher(conf, restart_method=restart_method)
  /opt/nova/lib/python3.10/site-packages/oslo_service/service.py(324)__init__()
-> super(ServiceLauncher, self).__init__(conf, restart_method=restart_method)
  /opt/nova/lib/python3.10/site-packages/oslo_service/service.py(259)__init__()
-> self.services = Services(restart_method=restart_method)
  /opt/nova/lib/python3.10/site-packages/oslo_service/service.py(747)__init__()->None
```

```python:/opt/nova/lib/python3.10/site-packages/oslo_service/service.py
737 class Services(object):
738     def __init__(self, restart_method="reload"):
739         if restart_method not in _LAUNCHER_RESTART_METHODS:
740             raise ValueError(_("Invalid restart_method: %s") % restart_method)
741         self.restart_method = restart_method
742         self.services = []
743         self.tg = threadgroup.ThreadGroup()
744         self.done = event.Event()
745
746     def add(self, service):
747         """Add a service to a list and create a thread to run it.
748
749         :param service: service to run
750         """
751         self.services.append(service)
752         self.tg.add_thread(self.run_service, service, self.done)
753
754     def stop(self):
755         """Wait for graceful shutdown of services and kill the threads."""
756         for service in self.services:
757             service.stop()
758
759         # Each service has performed cleanup, now signal that the run_service
760         # wrapper threads can now die:
761         if not self.done.ready():
762             self.done.send()
763
764         # reap threads:
765         self.tg.stop()
766
767     def wait(self):
768         """Wait for services to shut down."""
769         for service in self.services:
770             service.wait()
771         self.tg.wait()
```

rpcserver 初期化時の呼び出し元

```python:oslo_messaging/rpc/server.py
  /opt/nova/lib/python3.10/site-packages/eventlet/greenthread.py(221)main()
-> result = function(*args, **kwargs)
  /opt/nova/lib/python3.10/site-packages/oslo_service/service.py(806)run_service()
-> service.start()
  /opt/nova/lib/python3.10/site-packages/nova/service.py(194)start()
-> self.rpcserver = rpc.get_server(target, endpoints, serializer)
  /opt/nova/lib/python3.10/site-packages/nova/rpc.py(222)get_server()
-> return messaging.get_rpc_server(TRANSPORT,
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/server.py(234)get_rpc_server()
-> return server_cls(transport, target, dispatcher, executor)
> /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/server.py(141)__init__()
-> super(RPCServer, self).__init__(transport, dispatcher, executor)
```

nova-scheduler の select_destinations の呼び出し元

```
  /opt/nova/lib/python3.10/site-packages/eventlet/greenpool.py(88)_spawn_n_impl()
-> func(*args, **kwargs)
  /opt/nova/lib/python3.10/site-packages/futurist/_green.py(69)__call__()
-> self.work.run()
  /opt/nova/lib/python3.10/site-packages/futurist/_utils.py(45)run()
-> result = self.fn(*self.args, **self.kwargs)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/server.py(165)_process_incoming()
-> res = self.dispatcher.dispatch(message)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py(309)dispatch()
-> return self._do_dispatch(endpoint, method, ctxt, args)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py(229)_do_dispatch()
-> result = func(ctxt, **new_args)
  /opt/nova/lib/python3.10/site-packages/oslo_messaging/rpc/server.py(244)inner()
-> return func(*args, **kwargs)
> /opt/nova/lib/python3.10/site-packages/nova/scheduler/manager.py(144)select_destinations()
```

## periodic_task

```
$ find ./ -name '*.py' | xargs grep -A 3 '@periodic_task'
./scheduler/manager.py:    @periodic_task.periodic_task(
./scheduler/manager.py-        spacing=CONF.scheduler.discover_hosts_in_cells_interval, run_immediately=True
./scheduler/manager.py-    )
./scheduler/manager.py-    def _discover_hosts_in_cells(self, context):
```

- \_discover_hosts_in_cells
  - compute node を検出して cell にマッピングします
  - CONF.scheduler.discover_hosts_in_cells_interval(default=-1)
    - デフォルトは、-1 で無効になっています
    - この処理は新規ホストを追加した場合のみ必要な処理で、常時実行するのは無駄です
  - これを利用せずとも、compute node を新規追加する際に、nova-manage cell_v2 discover_hosts を一回実行すればよいだけです
  - 自動検出したい理由があるなら利用してもよいが、実際には不必要な場合がほとんどです
