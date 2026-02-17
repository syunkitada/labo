# monitoring-v1

- Grafana UI: http://dev01.pm.local.test:3000/
- VictoriaMetrics UI: http://dev01.pm.local.test:9999/vmui
- Kafka UI: http://dev01.pm.local.test:9090/
- Alertmanager: http://dev01.pm.local.test:9093/

Prometheus metrics endpoints

- vector-aggregator: localhost:9599/metrics
- vector-agent: localhost:9598/metrics
- node-exporter: localhost:9100/metrics

## Kafka Note

- [kafka: Introduction](https://kafka.apache.org/41/getting-started/introduction/)
- 概要
  - Kafkaは、Pub/Subモデルの分散メッセージキューです。
  - 用語
    - Producer: メッセージ送信側
      - ログを送る側
    - Consumer: メッセージ受信側
      - ログを読む側
    - Broker: メッセージ仲介役
      - Kafkaサーバ本体
    - Topic
      - メッセージキュー
    - Partition
      - Topicのキューをシャーディングしたキュー

## Vector

- [Vector: Introduction](https://vector.dev/docs/introduction/)
- 概要
  - Vectorは、Datadog社により開発されたログなどのデータ転送を行うためのOSSです。
  - Source（入力）、Transformer（加工）、Sink（出力）の3つの機能を持ち、データの転送処理を行います。
  - 各ノード上で稼働してログを収集する末端エージェントとして稼働したり、中継ノード上で稼働してログの集約やフィルタリングをしたりするブローカーのような役割もできます。
- 設定例
  - [赤帽エンジニアブログ: Vectorで遊ぶ](https://rheb.hatenablog.com/entry/vector)
