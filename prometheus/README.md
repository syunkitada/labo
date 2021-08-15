# prometheus

## 仕組み

- Prometheus(サーバ)
  - Scrape Job
    - Scrape Job を定義しておくことで、Prometheus は一定間隔ごとに Target の Scraping(メトリクスの Pull) を行う
    - Target は、静的に設定、もしくは SD(Service Discovery)によって自動登録することができる
  - Instance
    - Target は、Scrape のためのオブジェクトデータ
    - Instance は、Target を一意に識別するためのラベル
    - 一つの Target につき、一つの Instance が存在する
- Pushgateway
  - Prometheus は Pull のみをサポートしてるため、メトリクスの Push ができない
  - Pushgateway に Push でメトリクスを保存しておき、Prometheus は Pushgateway からメトリクスを Pull する
- Alertmanager
  - Alert はあらかじめ定義したルールに則って Prometheus によって発火され、Alertmanager へ送信される
  - Alertmanager は、受け取った Alert をグループに集約し、重複を排除し、silences(無視ルール) を適用し、throttles(抑制ルール)を適用し、アラートを送信する
  - 再送やクロージングのコントロールもする
- Exporter
  - メトリクスをエクスポートするエージェントの総称
  - Prometheus は Exporter からメトリクスを Pull する
  - Exporter には様々なものがある
    - https://prometheus.io/docs/instrumenting/exporters/
  - 自作してもよい
    - 基本的には、http でアクセスでき、特定のフォーマットでメトリクスを返せばよい
    - https://prometheus.io/docs/instrumenting/writing_exporters/

## HA 構成とスケーリングとフェデレーション

- Prometheus 自体は、単体でのみ動作し、クラスタリングによる HA の仕組みや、スケーリングの仕組みを持っていない
- HA 構成
  - 方法 1
    - 同じ設定の Prometheus を二台以上起動させる
    - どちらの Prometheus も同等のメトリクスを収集するので、どちらにアクセスしても同等の結果を得ることができる
    - ユーザは LB などを通して、Prometheus へアクセスする
    - 片系ダウンした場合、もう片系へアクセスして利用できる
      - ダウンした Prometheus は、その期間分のメトリクスを保存できない、復旧後もその期間分のメトリクスは欠けたままとなる
      - Prometheus は Pull しかできないため、データ同期する手段がない
  - 方法 2
    - Prometheus のデータ記憶領域に外部ストレージを利用する
    - ダウン時は別ノードで Prometheus を起動すればよいので、フェイルオーバーの時間も数秒で済む
- スケーリングとフェデレーション
  - 一つの Prometheus で、全 Target のメトリクスを収集するのではなく、複数の Prometheus で分担して収集する
  - これら複数の Prometheus をフェデレーションする Prometheus を用意する
  - 一つの Prometheus で扱える Target 数、メトリクス数の限界を把握し適切にキャパプラする必要がある

## タイムスタンプについて

- メトリクスのタイムスタンプは、Prometheus がメトリクスを保存するときに決定される
- Exporter や、Pushgateway では、メトリクスにタイムスタンプを設定することができない
- このためメトリクスのタイムスタンプは、若干のラグがあることに注意する

## メモ

- Prometheus は、Pull 型の TSDB であり、Push ができない
- Push ができないことの制約
  - メトリクスデータが欠けた場合、それを後で補填することができない
  - メトリクスデータの再計算ができない
    - メトリクスデータを集計して、別のメトリクスデータを生成するなど
- 監視目的での短期的なデータ利用は問題ないが、長期的なデータ保存には向いてない

## 参考

- [prometheus: configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
