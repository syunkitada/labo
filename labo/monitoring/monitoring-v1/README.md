# monitoring-v1

Grafana UI: http://dev01.pm.local.test:3000/
VictoriaMetrics UI: http://dev01.pm.local.test:9999/vmui
Kafka UI: http://dev01.pm.local.test:9090/
Alertmanager: http://dev01.pm.local.test:9093/

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
