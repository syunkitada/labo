# openapi まわり

- v3 のみ対象に見てく

```go:kubernetes/vendor/k8s.io/kube-aggregator/pkg/apiserver/apiserver.go
368 // PrepareRun prepares the aggregator to run, by setting up the OpenAPI spec and calling
369 // the generic PrepareRun.
...
370 func (s *APIAggregator) PrepareRun() (preparedAPIAggregator, error) {
395     if s.openAPIV3Config != nil && !s.skipOpenAPIInstallation {
396         if utilfeature.DefaultFeatureGate.Enabled(features.OpenAPIV3) {
397             s.OpenAPIV3VersionedService = routes.OpenAPI{
398                 Config: s.openAPIV3Config,
399             }.InstallV3(s.Handler.GoRestfulContainer, s.Handler.NonGoRestfulMux)
400         }
401     }
```

```go:kubernetes/staging/src/k8s.io/apiserver/pkg/server/routes/openapi.go
57 // InstallV3 adds the static group/versions defined in the RegisteredWebServices to the OpenAPI v3 spec
58 func (oa OpenAPI) InstallV3(c *restful.Container, mux *mux.PathRecorderMux) *handler3.OpenAPIService {
59     openAPIVersionedService, err := handler3.NewOpenAPIService(nil)
60     if err != nil {
61         klog.Fatalf("Failed to create OpenAPIService: %v", err)
62     }
63
64     err = openAPIVersionedService.RegisterOpenAPIV3VersionedService("/openapi/v3", mux)
65     if err != nil {
66         klog.Fatalf("Failed to register versioned open api spec for root: %v", err)
67     }
68
69     grouped := make(map[string][]*restful.WebService)
70
71     for _, t := range c.RegisteredWebServices() {
72         // Strip the "/" prefix from the name
73         gvName := t.RootPath()[1:]
74         grouped[gvName] = []*restful.WebService{t}
75     }
76
77     for gv, ws := range grouped {
78         spec, err := builder3.BuildOpenAPISpec(ws, oa.Config)
79         if err != nil {
80             klog.Errorf("Failed to build OpenAPI v3 for group %s, %q", gv, err)
81
82         }
83         openAPIVersionedService.UpdateGroupVersion(gv, spec)
84     }
85     return openAPIVersionedService
86 }
```
