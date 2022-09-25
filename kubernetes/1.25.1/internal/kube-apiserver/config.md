# config

- オブジェクトごとに Config が用意されてる
- Complete によってバリデートやデフォ値の補完をやって完全な Config(CompletedConfig)を返す
- CompletedConfig の New によって目的のオブジェクトが返される

```
539 // Complete fills in any fields not set that are required to have valid data and can be derived
540 // from other fields. If you're going to `ApplyOptions`, do that first. It's mutating the receiver.
541 func (c *Config) Complete(informers informers.SharedInformerFactory) CompletedConfig {
...
586     return CompletedConfig{&completedConfig{c, informers}}
587 }
...

595 // New creates a new server which logically combines the handling chain with the passed server.
596 // name is used to differentiate for logging. The handler chain in particular can be difficult as it starts delegating.
597 // delegationTarget may not be nil.
598 func (c completedConfig) New(name string, delegationTarget DelegationTarget) (*GenericAPIServer, error) {
...
799     return s, nil
800 }
```
