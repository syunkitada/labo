# handler (http.Handler まわり)

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/config.go
595 // New creates a new server which logically combines the handling chain with the passed server.
596 // name is used to differentiate for logging. The handler chain in particular can be difficult as it starts delegating.
597 // delegationTarget may not be nil.
598 func (c completedConfig) New(name string, delegationTarget DelegationTarget) (*GenericAPIServer, error) {
599     if c.Serializer == nil {
600         return nil, fmt.Errorf("Genericapiserver.New() called with config.Serializer == nil")
601     }
602     if c.LoopbackClientConfig == nil {
603         return nil, fmt.Errorf("Genericapiserver.New() called with config.LoopbackClientConfig == nil")
604     }
605     if c.EquivalentResourceRegistry == nil {
606         return nil, fmt.Errorf("Genericapiserver.New() called with config.EquivalentResourceRegistry == nil")
607     }
608
609     handlerChainBuilder := func(handler http.Handler) http.Handler {
610         return c.BuildHandlerChainFunc(handler, c.Config)
611     }
612
613     apiServerHandler := NewAPIServerHandler(name, c.Serializer, handlerChainBuilder, delegationTarget.UnprotectedHandler())
614
615     s := &GenericAPIServer{
616         discoveryAddresses:         c.DiscoveryAddresses,
617         LoopbackClientConfig:       c.LoopbackClientConfig,
618         legacyAPIGroupPrefixes:     c.LegacyAPIGroupPrefixes,
619         admissionControl:           c.AdmissionControl,
620         Serializer:                 c.Serializer,
621         AuditBackend:               c.AuditBackend,
622         Authorizer:                 c.Authorization.Authorizer,
623         delegationTarget:           delegationTarget,
624         EquivalentResourceRegistry: c.EquivalentResourceRegistry,
625         HandlerChainWaitGroup:      c.HandlerChainWaitGroup,
626         Handler:                    apiServerHandler,
...
```

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/genericapiserver.go

100 // GenericAPIServer contains state for a Kubernetes cluster api server.
101 type GenericAPIServer struct {
...
135     Handler *APIServerHandler
...

```

- ライブラリメモ
  - https://github.com/emicklei/go-restful

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/handler.go
 37 // APIServerHandlers holds the different http.Handlers used by the API server.
 38 // This includes the full handler chain, the director (which chooses between gorestful and nonGoRestful,
 39 // the gorestful handler (used for the API) which falls through to the nonGoRestful handler on unregistered paths,
 40 // and the nonGoRestful handler (which can contain a fallthrough of its own)
 41 // FullHandlerChain -> Director -> {GoRestfulContainer,NonGoRestfulMux} based on inspection of registered web services
 42 type APIServerHandler struct {
 43     // FullHandlerChain is the one that is eventually served with.  It should include the full filter
 44     // chain and then call the Director.
 45     FullHandlerChain http.Handler
 46     // The registered APIs.  InstallAPIs uses this.  Other servers probably shouldn't access this directly.
 47     GoRestfulContainer *restful.Container
 48     // NonGoRestfulMux is the final HTTP handler in the chain.
 49     // It comes after all filters and the API handling
 50     // This is where other servers can attach handler to various parts of the chain.
 51     NonGoRestfulMux *mux.PathRecorderMux
 52
 53     // Director is here so that we can properly handle fall through and proxy cases.
 54     // This looks a bit bonkers, but here's what's happening.  We need to have /apis handling registered in gorestful in order to have
 55     // swagger generated for compatibility.  Doing that with `/apis` as a webservice, means that it forcibly 404s (no defaulting allowed)
 56     // all requests which are not /apis or /apis/.  We need those calls to fall through behind goresful for proper delegation.  Trying to
 57     // register for a pattern which includes everything behind it doesn't work because gorestful negotiates for verbs and content encoding
 58     // and all those things go crazy when gorestful really just needs to pass through.  In addition, openapi enforces unique verb constraints
 59     // which we don't fit into and it still muddies up swagger.  Trying to switch the webservices into a route doesn't work because the
 60     //  containing webservice faces all the same problems listed above.
 61     // This leads to the crazy thing done here.  Our mux does what we need, so we'll place it in front of gorestful.  It will introspect to
 62     // decide if the route is likely to be handled by goresful and route there if needed.  Otherwise, it goes to NonGoRestfulMux mux in
 63     // order to handle "normal" paths and delegation. Hopefully no API consumers will ever have to deal with this level of detail.  I think
 64     // we should consider completely removing gorestful.
 65     // Other servers should only use this opaquely to delegate to an API server.
 66     Director http.Handler
 67 }

 73 func NewAPIServerHandler(name string, s runtime.NegotiatedSerializer, handlerChainBuilder HandlerChainBuilderFn, notFoundHandler http.Handler) *APIServerH    andler {
 74     nonGoRestfulMux := mux.NewPathRecorderMux(name)
 75     if notFoundHandler != nil {
 76         nonGoRestfulMux.NotFoundHandler(notFoundHandler)
 77     }
 78
 79     gorestfulContainer := restful.NewContainer()
 80     gorestfulContainer.ServeMux = http.NewServeMux()
 81     gorestfulContainer.Router(restful.CurlyRouter{}) // e.g. for proxy/{kind}/{name}/{*}
 82     gorestfulContainer.RecoverHandler(func(panicReason interface{}, httpWriter http.ResponseWriter) {
 83         logStackOnRecover(s, panicReason, httpWriter)
 84     })
 85     gorestfulContainer.ServiceErrorHandler(func(serviceErr restful.ServiceError, request *restful.Request, response *restful.Response) {
 86         serviceErrorHandler(s, serviceErr, request, response)
 87     })
 88
 89     director := director{
 90         name:               name,
 91         goRestfulContainer: gorestfulContainer,
 92         nonGoRestfulMux:    nonGoRestfulMux,
 93     }
 94
 95     return &APIServerHandler{
 96         FullHandlerChain:   handlerChainBuilder(director),
 97         GoRestfulContainer: gorestfulContainer,
 98         NonGoRestfulMux:    nonGoRestfulMux,
 99         Director:           director,
100     }
101 }
```

- ServeHTTP: ハンドラの entrypoint

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/handler.go
187 // ServeHTTP makes it an http.Handler
188 func (a *APIServerHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
189     a.FullHandlerChain.ServeHTTP(w, r)
190 }
```

- DefaultBuildHandlerChain に director を入れると、いろいろ設定されて返ってくる
- 認証系やトレーサなどをここで仕込んでる？
- ミドルウェアに近いと思う

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/config.go
609     handlerChainBuilder := func(handler http.Handler) http.Handler {
610         return c.BuildHandlerChainFunc(handler, c.Config)
611     }
...
329     return &Config{
330         Serializer:                  codecs,
331         BuildHandlerChainFunc:       DefaultBuildHandlerChain,
...
808 func DefaultBuildHandlerChain(apiHandler http.Handler, c *Config) http.Handler {
809     handler := filterlatency.TrackCompleted(apiHandler)
810     handler = genericapifilters.WithAuthorization(handler, c.Authorization.Authorizer, c.Serializer)
811     handler = filterlatency.TrackStarted(handler, "authorization")
...
859     handler = genericfilters.WithHTTPLogging(handler)
860     if utilfeature.DefaultFeatureGate.Enabled(genericfeatures.APIServerTracing) {
861         handler = genericapifilters.WithTracing(handler, c.TracerProvider)
862     }
863     handler = genericapifilters.WithLatencyTrackers(handler)
864     handler = genericapifilters.WithRequestInfo(handler, c.RequestInfoResolver)
865     handler = genericapifilters.WithRequestReceivedTimestamp(handler)
866     handler = genericapifilters.WithMuxAndDiscoveryComplete(handler, c.lifecycleSignals.MuxAndDiscoveryComplete.Signaled())
867     handler = genericfilters.WithPanicRecovery(handler, c.RequestInfoResolver)
868     handler = genericapifilters.WithAuditID(handler)
869     return handler
870 }
```

- ルーティングの本体は director の ServeHTTP

```go:staging/src/k8s.io/apiserver/pkg/server/handler.go
 69 // HandlerChainBuilderFn is used to wrap the GoRestfulContainer handler using the provided handler chain.
 70 // It is normally used to apply filtering like authentication and authorization
 71 type HandlerChainBuilderFn func(apiHandler http.Handler) http.Handler

116 type director struct {
117     name               string
118     goRestfulContainer *restful.Container
119     nonGoRestfulMux    *mux.PathRecorderMux
120 }
121
122 func (d director) ServeHTTP(w http.ResponseWriter, req *http.Request) {
123     path := req.URL.Path
124
125     // check to see if our webservices want to claim this path
126     for _, ws := range d.goRestfulContainer.RegisteredWebServices() {
127         switch {
128         case ws.RootPath() == "/apis":
129             // if we are exactly /apis or /apis/, then we need special handling in loop.
130             // normally these are passed to the nonGoRestfulMux, but if discovery is enabled, it will go directly.
131             // We can't rely on a prefix match since /apis matches everything (see the big comment on Director above)
132             if path == "/apis" || path == "/apis/" {
133                 klog.V(5).Infof("%v: %v %q satisfied by gorestful with webservice %v", d.name, req.Method, path, ws.RootPath())
134                 // don't use servemux here because gorestful servemuxes get messed up when removing webservices
135                 // TODO fix gorestful, remove TPRs, or stop using gorestful
136                 d.goRestfulContainer.Dispatch(w, req)
137                 return
138             }
139
140         case strings.HasPrefix(path, ws.RootPath()):
141             // ensure an exact match or a path boundary match
// pathがws.RootPathを持ってれば、goresfulを呼んで、そうでなければnonGoRestfulを呼ぶ
142             if len(path) == len(ws.RootPath()) || path[len(ws.RootPath())] == '/' {
143                 klog.V(5).Infof("%v: %v %q satisfied by gorestful with webservice %v", d.name, req.Method, path, ws.RootPath())
144                 // don't use servemux here because gorestful servemuxes get messed up when removing webservices
145                 // TODO fix gorestful, remove TPRs, or stop using gorestful
146                 d.goRestfulContainer.Dispatch(w, req)
147                 return
148             }
149         }
150     }
151
152     // if we didn't find a match, then we just skip gorestful altogether
153     klog.V(5).Infof("%v: %v %q satisfied by nonGoRestful", d.name, req.Method, path)
154     d.nonGoRestfulMux.ServeHTTP(w, req)
155 }
```

RegisteredWebServices(goresful) の一覧

director は 2 種類ある
一回のリクエストでその 2 種類の director の ServeHTTP を通る

```
126     for _, ws := range d.goRestfulContainer.RegisteredWebServices() {
            fmt.Println(ws.RootPath())
```

一つ目の RegisteredWebServices(goresful)

```
/version
/apis/apiregistration.k8s.io/v1
/apis/apiregistration.k8s.io
```

二つ目の RegisteredWebServices(goresful)

```
/version
/apis
/logs
/.well-known/openid-configuration
/openid/v1/jwks
/api/v1
/api
/apis/authentication.k8s.io/v1
/apis/authentication.k8s.io
/apis/authorization.k8s.io/v1
/apis/authorization.k8s.io
/apis/autoscaling/v1
/apis/autoscaling/v2
/apis/autoscaling/v2beta2
/apis/autoscaling
/apis/batch/v1
/apis/batch
/apis/certificates.k8s.io/v1
/apis/certificates.k8s.io
/apis/coordination.k8s.io/v1
/apis/coordination.k8s.io
/apis/discovery.k8s.io/v1
/apis/discovery.k8s.io
/apis/networking.k8s.io/v1
/apis/networking.k8s.io
/apis/node.k8s.io/v1
/apis/node.k8s.io
/apis/policy/v1
/apis/policy
/apis/rbac.authorization.k8s.io/v1
/apis/rbac.authorization.k8s.io
/apis/scheduling.k8s.io/v1
/apis/scheduling.k8s.io
/apis/storage.k8s.io/v1
/apis/storage.k8s.io/v1beta1
/apis/storage.k8s.io
/apis/flowcontrol.apiserver.k8s.io/v1beta1
/apis/flowcontrol.apiserver.k8s.io/v1beta2
/apis/flowcontrol.apiserver.k8s.io
/apis/apps/v1
/apis/apps
/apis/admissionregistration.k8s.io/v1
/apis/admissionregistration.k8s.io
/apis/events.k8s.io/v1
/apis/events.k8s.io
```

- openapi の path は以下でアクセスされる(nonGoRestful)
- リクエストのたびに先にここをたたいて API の spec を拾ってる?

```
/openapi/v2
/openapi/v3
```

```
 34 // PathRecorderMux wraps a mux object and records the registered exposedPaths.
 35 type PathRecorderMux struct {
 36     // name is used for logging so you can trace requests through
 37     name string
 38
 39     lock            sync.Mutex
 40     notFoundHandler http.Handler
 41     pathToHandler   map[string]http.Handler
 42     prefixToHandler map[string]http.Handler
 43
 44     // mux stores a pathHandler and is used to handle the actual serving.
 45     // Turns out, we want to accept trailing slashes, BUT we don't care about handling
 46     // everything under them.  This does exactly matches only unless its explicitly requested to
 47     // do something different
 48     mux atomic.Value
 49
 50     // exposedPaths is the list of paths that should be shown at /
 51     exposedPaths []string
 52
 53     // pathStacks holds the stacks of all registered paths.  This allows us to show a more helpful message
 54     // before the "http: multiple registrations for %s" panic.
 55     pathStacks map[string]string
 56 }
```
