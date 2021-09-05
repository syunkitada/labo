# Prometheus HA 構成

## システム構成

- scraper
  - データの永続化は必要としない
  - データの保持期間は短期間でよい
  - 二台一セットで、同じ exporter のグループ(exporters)から scraper を行う
- pushgateway
  - データの永続化は必要としない
  - 二台一セットで、vip に束ねるなどして、pusher は定期的にどちらかの pushgateway にメトリクスを保存する
- prometheus は一定期間（5 分間）メトリクスの取得ができなくなると、ないものとして扱うため、scrape や push もそれ以内に行うとよい
  - 一般的には、1 分や、30 秒ごとに scraper や push を行うとよい
- federator
  - 二台一セットで、各 scraper、各 pushgateway からメトリクスを scrape する
    - scrape するときに vip などを通してはいけない
  - データの永続化を必要とする
    - アラートの評価には一定期間のメトリクスを必要とするため、最低限その期間分のメトリクスは永続化すべき
- alertmanager
  - 二台一セットで、federator からのアラート通知を受け取り、抑制などして適切なシステムへ通知を行う
  - notificationLog と silences の冗長化のため、バックアップ用途として別途 alertmanager を 1 台クラスタに参加させる
    - これはバックアップ用途で、prometheus から notify も受け取らないし、その通知も行わない

```
exporters <-- pull metrics -- prometheus-scraper1-1 ＼
                           ×
exporters <-- pull metrics -- prometheus-scraper1-2 ＼

exporters <-- pull metrics -- prometheus-scraper2-1 ＼
                           ×
exporters <-- pull metrics -- prometheus-scraper2-2 <- pull metrics -- prometheus-federator1-1 -- notify --> alertmanager1-1 -- notify -->
                                                                    ×                          ×               |
exporters <-- pull metrics -- prometheus-scraper3-1 <- pull metrics -- prometheus-federator1-2 -- notify --> alertmanager1-2 -- notify -->
                           ×                                                                                    |
exporters <-- pull metrics -- prometheus-scraper3-2 ／                                                           |
                                                                                                                 |
exporters <-- pull metrics -- prometheus-scraper4-1 ／                                                           |
                           ×                                                                                    |
exporters <-- pull metrics -- prometheus-scraper4-2 ／                                                           |
                                                                                                                 |
pushers -- push metrics --> vip -- pushgateway1-1   ／                                                           |
pushers -- push metrics -->     ＼ pushgateway1-2   ／                                                           |
                                                                                                                 |
pushers -- push metrics --> vip -- pushgateway2-1   ／                                                           |
pushers -- push metrics -->     ＼ pushgateway2-2   ／                                                           |
                                                                                                                 |
                                                                                                             alertmanager1-3
```
