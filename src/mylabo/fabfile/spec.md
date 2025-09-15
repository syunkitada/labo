# 仕様書

## 用語

- spec
  - yaml で書かれた実験環境の仕様書のことです
- resource_spec(コード内表記=rspec)
  - spec 内に定義された各 resource の仕様書のことです
- resource
  - vm や container などの環境の実態のことです
  - resource には、大まかに３つの種別があります
    - infra
      - node を管理するための基盤となる resource です
    - image
      - node で利用する image の resource です
    - node
      - vm や container などの resource です
- resource_module
  - resource を作成するモジュールのことです
- runtime_context(コード内表記=c)
  - コマンド実行のためのコンテキストです
  - invoke の Context もしくは、fabric の Connection のことです
    - ローカル実行の場合は invoke の Context が作成され、リモート実行の場合は fabric の Connection が作成され、利用されます
    - fabric は、runtime として invoke を使ってるため、fabric の Connection は invoke の Context とある程度の互換性があります
      - どちらも run, sudo といったメソッドを持っており、これによってコマンドを実行することができます
      - 実装時にどちらのコンテキストを利用してるかを意識する必要はありません
- task(コード内表記=t)
  - resource を作成するための実行タスクのことです
  - この task を resource_module に渡すことで resource が作成されます
  - task には spec, rspec, c などが内蔵されています
- resource_context(コード内表記=rc)
  - 各 resource のコンテキストです
  - task を内包しています
  - 単純なリソースの場合には、これを持たず task のみで resource を制御します

## spec(yaml) のフォーマット

```
# 他のspecをimportして設定を引き継ぎます
imports
  ...

# 汎用設定
common:
  ...

# resourceのテンプレートの定義場所
template_map:
  ...

# ipamの定義場所
ipam:
  ...

# infra resource の定義場所
infra_map:
  ...

# image resource の定義場所
vm_image_map:
  ...

# node resource の定義場所
nodes:
  ...

# node resource の上書き用の定義
node_map:
  ...
```
