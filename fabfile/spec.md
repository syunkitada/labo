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
- resource_context(コード内表記=ctx)
  - 各リソースのコンテキストです
  - runtime_context を内包しています
- task
  - resource を作成するための実行タスクのことです
  - この task を resource_module に渡すことで resource が作成されます
  - task には spec, resource_spec, runtime_context, resource_context などが内蔵されています
