# entrypoint

- entrypoint から、server.Serve までのコード抜粋

```
# entrypoint
$ go run -mod vendor cmd/kube-apiserver/apiserver.go ...
```

```go:cmd/kube-apiserver/apiserver.go
 19 package main
 20
 21 import (
 22     "os"
 23     _ "time/tzdata" // for timeZone support in CronJob
 24
 25     "k8s.io/component-base/cli"
 26     _ "k8s.io/component-base/logs/json/register"          // for JSON log format registration
 27     _ "k8s.io/component-base/metrics/prometheus/clientgo" // load all the prometheus client-go plugins
 28     _ "k8s.io/component-base/metrics/prometheus/version"  // for version metric registration
 29     "k8s.io/kubernetes/cmd/kube-apiserver/app"
 30 )
 31
 32 func main() {
 33     command := app.NewAPIServerCommand()
 34     code := cli.Run(command)
 35     os.Exit(code)
 36 }
```

- CreateServerChain で http.Handler の chain を組み立ててる
  - リクエストがくると、apiExtensionsServer の director の ServeHTTP が呼ばれて、その後 kubeAPIServer の director の ServeHTTP が呼ばれる

```go:cmd/kube-apiserver/app/server.go
91 // NewAPIServerCommand creates a *cobra.Command object with default parameters
92 func NewAPIServerCommand() *cobra.Command {
...
109         RunE: func(cmd *cobra.Command, args []string) error {
110             verflag.PrintAndExitIfRequested()
111             fs := cmd.Flags()
112
113             // Activate logging as soon as possible, after that
114             // show flags with the final logging configuration.
115             if err := logsapi.ValidateAndApply(s.Logs, utilfeature.DefaultFeatureGate); err != nil {
116                 return err
117             }
118             cliflag.PrintFlags(fs)
119
120             // set default options
121             completedOptions, err := Complete(s)
122             if err != nil {
123                 return err
124             }
125
126             // validate options
127             if errs := completedOptions.Validate(); len(errs) != 0 {
128                 return utilerrors.NewAggregate(errs)
129             }
130
131             return Run(completedOptions, genericapiserver.SetupSignalHandler())
132         },

158 // Run runs the specified APIServer.  This should never exit.
159 func Run(completeOptions completedServerRunOptions, stopCh <-chan struct{}) error {
160     // To help debugging, immediately log version
161     klog.Infof("Version: %+v", version.Get())
162
163     klog.InfoS("Golang settings", "GOGC", os.Getenv("GOGC"), "GOMAXPROCS", os.Getenv("GOMAXPROCS"), "GOTRACEBACK", os.Getenv("GOTRACEBACK"))          164
165     server, err := CreateServerChain(completeOptions)
166     if err != nil {
167         return err
168     }
169
170     prepared, err := server.PrepareRun()
171     if err != nil {
172         return err
173     }
174
175     return prepared.Run(stopCh)
176 }
...
178 // CreateServerChain creates the apiservers connected via delegation.
179 func CreateServerChain(completedOptions completedServerRunOptions) (*aggregatorapiserver.APIAggregator, error) {
...
192     notFoundHandler := notfoundhandler.New(kubeAPIServerConfig.GenericConfig.Serializer, genericapifilters.NoMuxAndDiscoveryIncompleteKey)
193     apiExtensionsServer, err := createAPIExtensionsServer(apiExtensionsConfig, genericapiserver.NewEmptyDelegateWithCustomHandler(notFoundHandler))
194     if err != nil {
195         return nil, err
196     }
197
198     kubeAPIServer, err := CreateKubeAPIServer(kubeAPIServerConfig, apiExtensionsServer.GenericAPIServer)
199     if err != nil {
200         return nil, err
201     }
202
203     // aggregator comes last in the chain
204     aggregatorConfig, err := createAggregatorConfig(*kubeAPIServerConfig.GenericConfig, completedOptions.ServerRunOptions, kubeAPIServerConfig.ExtraConfig    .VersionedInformers, serviceResolver, kubeAPIServerConfig.ExtraConfig.ProxyTransport, pluginInitializer)
205     if err != nil {
206         return nil, err
207     }
208     aggregatorServer, err := createAggregatorServer(aggregatorConfig, kubeAPIServer.GenericAPIServer, apiExtensionsServer.Informers)
209     if err != nil {
210         // we don't need special handling for innerStopCh because the aggregator server doesn't create any go routines
211         return nil, err
212     }
213
214     return aggregatorServer, nil
215 }


217 // CreateKubeAPIServer creates and wires a workable kube-apiserver
218 func CreateKubeAPIServer(kubeAPIServerConfig *controlplane.Config, delegateAPIServer genericapiserver.DelegationTarget) (*controlplane.Instance, error) {
219     kubeAPIServer, err := kubeAPIServerConfig.Complete().New(delegateAPIServer)
220     if err != nil {
221         return nil, err
222     }
223
224     return kubeAPIServer, nil
225 }
```

```go:kubernetes/pkg/controlplane/instance.go
332 func (c completedConfig) New(delegationTarget genericapiserver.DelegationTarget) (*Instance, error) {
333     if reflect.DeepEqual(c.ExtraConfig.KubeletClientConfig, kubeletclient.KubeletClientConfig{}) {
334         return nil, fmt.Errorf("Master.New() called with empty config.KubeletClientConfig")
335     }
336
337     s, err := c.GenericConfig.New("kube-apiserver", delegationTarget)
338     if err != nil {
339         return nil, err
340     }
...
377     m := &Instance{
378         GenericAPIServer:          s,
379         ClusterAuthenticationInfo: c.ExtraConfig.ClusterAuthenticationInfo,
380     }
...
498     return m, nil
499 }
```

```go:cmd/kube-apiserver/app/aggregator.go
 56 func createAggregatorConfig(
 57     kubeAPIServerConfig genericapiserver.Config,
 58     commandOptions *options.ServerRunOptions,
 59     externalInformers kubeexternalinformers.SharedInformerFactory,
 60     serviceResolver aggregatorapiserver.ServiceResolver,
 61     proxyTransport *http.Transport,
 62     pluginInitializers []admission.PluginInitializer,
 63 ) (*aggregatorapiserver.Config, error) {
...
108     aggregatorConfig := &aggregatorapiserver.Config{
109         GenericConfig: &genericapiserver.RecommendedConfig{
110             Config:                genericConfig,
111             SharedInformerFactory: externalInformers,
112         },
113         ExtraConfig: aggregatorapiserver.ExtraConfig{
114             ProxyClientCertFile:       commandOptions.ProxyClientCertFile,
115             ProxyClientKeyFile:        commandOptions.ProxyClientKeyFile,
116             ServiceResolver:           serviceResolver,
117             ProxyTransport:            proxyTransport,
118             RejectForwardingRedirects: commandOptions.AggregatorRejectForwardingRedirects,
119         },
120     }
...
125     return aggregatorConfig, nil
126 }
...
128 func createAggregatorServer(aggregatorConfig *aggregatorapiserver.Config, delegateAPIServer genericapiserver.DelegationTarget, apiExtensionInformers apiex    tensionsinformers.SharedInformerFactory) (*aggregatorapiserver.APIAggregator, error) {
129     aggregatorServer, err := aggregatorConfig.Complete().NewWithDelegate(delegateAPIServer)
130     if err != nil {
131         return nil, err
132     }
...
173     return aggregatorServer, nil
174 }
```

```go:kubernetes/vendor/k8s.io/kube-aggregator/pkg/apiserver/apiserver.go
181 // NewWithDelegate returns a new instance of APIAggregator from the given config.
182 func (c completedConfig) NewWithDelegate(delegationTarget genericapiserver.DelegationTarget) (*APIAggregator, error) {
183     genericServer, err := c.GenericConfig.New("kube-aggregator", delegationTarget)
184     if err != nil {
185         return nil, err
186     }
...
207     s := &APIAggregator{
208         GenericAPIServer:           genericServer,
209         delegateHandler:            delegationTarget.UnprotectedHandler(),
210         proxyTransport:             c.ExtraConfig.ProxyTransport,
211         proxyHandlers:              map[string]*proxyHandler{},
212         handledGroups:              sets.String{},
213         lister:                     informerFactory.Apiregistration().V1().APIServices().Lister(),
214         APIRegistrationInformers:   informerFactory,
215         serviceResolver:            c.ExtraConfig.ServiceResolver,
216         openAPIConfig:              c.GenericConfig.OpenAPIConfig,
217         openAPIV3Config:            c.GenericConfig.OpenAPIV3Config,
218         egressSelector:             c.GenericConfig.EgressSelector,
219         proxyCurrentCertKeyContent: func() (bytes []byte, bytes2 []byte) { return nil, nil },
220         rejectForwardingRedirects:  c.ExtraConfig.RejectForwardingRedirects,
221     }
...
365     return s, nil
366 }


114 // preparedGenericAPIServer is a private wrapper that enforces a call of PrepareRun() before Run can be invoked.
115 type preparedAPIAggregator struct {
116     *APIAggregator
117     runnable runnable
118 }
...

368 // PrepareRun prepares the aggregator to run, by setting up the OpenAPI spec and calling
369 // the generic PrepareRun.
370 func (s *APIAggregator) PrepareRun() (preparedAPIAggregator, error) {
...
386     prepared := s.GenericAPIServer.PrepareRun()

415     return preparedAPIAggregator{APIAggregator: s, runnable: prepared}, nil
416 }
...
418 func (s preparedAPIAggregator) Run(stopCh <-chan struct{}) error {
419     return s.runnable.Run(stopCh)
420 }
```

- GenericAPIServer の Handler が http.Handler

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/genericapiserver.go

100 // GenericAPIServer contains state for a Kubernetes cluster api server.
101 type GenericAPIServer struct {
...
135     Handler *APIServerHandler
...

380 // preparedGenericAPIServer is a private wrapper that enforces a call of PrepareRun() before Run can be invoked.
381 type preparedGenericAPIServer struct {
382     *GenericAPIServer
383 }
384
385 // PrepareRun does post API installation setup steps. It calls recursively the same function of the delegates.
386 func (s *GenericAPIServer) PrepareRun() preparedGenericAPIServer {
...
414     return preparedGenericAPIServer{s}
415 }

459 func (s preparedGenericAPIServer) Run(stopCh <-chan struct{}) error {
...

534     stoppedCh, listenerStoppedCh, err := s.NonBlockingRun(stopHttpServerCh, shutdownTimeout)
535     if err != nil {
536         return err
537     }
...
585     klog.V(1).Info("[graceful-termination] waiting for shutdown to be initiated")
586     <-stopCh
587
588     // run shutdown hooks directly. This includes deregistering from
589     // the kubernetes endpoint in case of kube-apiserver.
590     func() {
591         defer func() {
592             preShutdownHooksHasStoppedCh.Signal()
593             klog.V(1).InfoS("[graceful-termination] pre-shutdown hooks completed", "name", preShutdownHooksHasStoppedCh.Name())
594         }()
595         err = s.RunPreShutdownHooks()
596     }()
597     if err != nil {
598         return err
599     }
600
601     // Wait for all requests in flight to drain, bounded by the RequestTimeout variable.
602     <-drainedCh.Signaled()
603
604     if s.AuditBackend != nil {
605         s.AuditBackend.Shutdown()
606         klog.V(1).InfoS("[graceful-termination] audit backend shutdown completed")
607     }
608
609     // wait for stoppedCh that is closed when the graceful termination (server.Shutdown) is finished.
610     <-listenerStoppedCh
611     <-stoppedCh
612
613     klog.V(1).Info("[graceful-termination] apiserver is exiting")
614     return nil
615 }


617 // NonBlockingRun spawns the secure http server. An error is
618 // returned if the secure port cannot be listened on.
619 // The returned channel is closed when the (asynchronous) termination is finished.
620 func (s preparedGenericAPIServer) NonBlockingRun(stopCh <-chan struct{}, shutdownTimeout time.Duration) (<-chan struct{}, <-chan struct{}, error) {
621     // Use an internal stop channel to allow cleanup of the listeners on error.
622     internalStopCh := make(chan struct{})
623     var stoppedCh <-chan struct{}
624     var listenerStoppedCh <-chan struct{}
625     if s.SecureServingInfo != nil && s.Handler != nil {
626         var err error
627         stoppedCh, listenerStoppedCh, err = s.SecureServingInfo.Serve(s.Handler, shutdownTimeout, internalStopCh)
628         if err != nil {
629             close(internalStopCh)
630             return nil, nil, err
631         }
632     }
633
634     // Now that listener have bound successfully, it is the
635     // responsibility of the caller to close the provided channel to
636     // ensure cleanup.
637     go func() {
638         <-stopCh
639         close(internalStopCh)
640     }()
641
642     s.RunPostStartHooks(stopCh)
643
644     if _, err := systemd.SdNotify(true, "READY=1\n"); err != nil {
645         klog.Errorf("Unable to send systemd daemon successful start message: %v\n", err)
646     }
647
648     return stoppedCh, listenerStoppedCh, nil
649 }
```

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/secure_serving.go
151 // Serve runs the secure http server. It fails only if certificates cannot be loaded or the initial listen call fails.
152 // The actual server loop (stoppable by closing stopCh) runs in a go routine, i.e. Serve does not block.
153 // It returns a stoppedCh that is closed when all non-hijacked active requests have been processed.
154 // It returns a listenerStoppedCh that is closed when the underlying http Server has stopped listening.
155 func (s *SecureServingInfo) Serve(handler http.Handler, shutdownTimeout time.Duration, stopCh <-chan struct{}) (<-chan struct{}, <-chan struct{}, error) {
156     if s.Listener == nil {
157         return nil, nil, fmt.Errorf("listener must not be nil")
158     }
159
160     tlsConfig, err := s.tlsConfig(stopCh)
161     if err != nil {
162         return nil, nil, err
163     }
164
165     secureServer := &http.Server{
166         Addr:           s.Listener.Addr().String(),
167         Handler:        handler,
168         MaxHeaderBytes: 1 << 20,
169         TLSConfig:      tlsConfig,
170
171         IdleTimeout:       90 * time.Second, // matches http.DefaultTransport keep-alive timeout
172         ReadHeaderTimeout: 32 * time.Second, // just shy of requestTimeoutUpperBound
173     }
...
211     return RunServer(secureServer, s.Listener, shutdownTimeout, stopCh)
212 }
...
220 func RunServer(
221     server *http.Server,
222     ln net.Listener,
223     shutDownTimeout time.Duration,
224     stopCh <-chan struct{},
225 ) (<-chan struct{}, <-chan struct{}, error) {
240     go func() {
241         defer utilruntime.HandleCrash()
242         defer close(listenerStoppedCh)
243
244         var listener net.Listener
245         listener = tcpKeepAliveListener{ln}
246         if server.TLSConfig != nil {
247             listener = tls.NewListener(listener, server.TLSConfig)
248         }
249
250         err := server.Serve(listener)
251
252         msg := fmt.Sprintf("Stopped listening on %s", ln.Addr().String())
253         select {
254         case <-stopCh:
255             klog.Info(msg)
256         default:
257             panic(fmt.Sprintf("%s due to error: %v", msg, err))
258         }
259     }()
260
261     return serverShutdownCh, listenerStoppedCh, nil
262 }
```
