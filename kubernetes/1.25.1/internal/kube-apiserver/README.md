# kube-apiserver

```
# entrypoint
$ go run -mod vendor cmd/kube-apiserver/apiserver.go -h
```

- https://github.com/kubernetes/sample-apiserver

```
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

178 // CreateServerChain creates the apiservers connected via delegation.
179 func CreateServerChain(completedOptions completedServerRunOptions) (*aggregatorapiserver.APIAggregator, error) {
208     aggregatorServer, err := createAggregatorServer(aggregatorConfig, kubeAPIServer.GenericAPIServer, apiExtensionsServer.Informers)
...
214     return aggregatorServer, nil
215 }
```
