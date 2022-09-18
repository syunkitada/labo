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
1
```
