# DEBUG

## Prometheus から Alertmanager へのリクエスト

- 以下のメトリクス、アラートルール によってアラートを発生したときの Alertmanager へのリクエストを見る

メトリクスの実態

```
check2{output="warningout"} 1
```

アラートルール

```
  - alert: check2
    expr: check2{job="myjob"} > 0
    for: 5s
    labels:
      severity: warning
    annotations:
      summary: check2 alert summary
```

```
# alertmanagerのport 9093 でデバックする
./http-debug-server.py 9093

```

```
INFO:root:POST request,
Path: /api/v2/alerts
Headers:
Host: localhost:9093
User-Agent: Prometheus/2.29.1
Content-Length: 350
Content-Type: application/json

Body:
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-22T07:06:54.913Z","startsAt":"2021-08-22T06:47:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]

127.0.0.1 - - [22/Aug/2021 16:02:54] "POST /api/v2/alerts HTTP/1.1" 200 -



INFO:root:POST request,
Path: /api/v2/alerts
Headers:
Host: localhost:9093
User-Agent: Prometheus/2.29.1
Content-Length: 350
Content-Type: application/json

Body:
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-22T07:08:09.913Z","startsAt":"2021-08-22T06:47:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]

127.0.0.1 - - [22/Aug/2021 16:04:09] "POST /api/v2/alerts HTTP/1.1" 200 -



INFO:root:POST request,
Path: /api/v2/alerts
Headers:
Host: localhost:9093
User-Agent: Prometheus/2.29.1
Content-Length: 350
Content-Type: application/json

Body:
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-22T07:09:24.913Z","startsAt":"2021-08-22T06:47:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]

127.0.0.1 - - [22/Aug/2021 16:05:24] "POST /api/v2/alerts HTTP/1.1" 200 -
```

## webhook

- 抑制しないと、Prometheus から Alert が送られるたびにアラートが通知される

```
127.0.0.1 - - [22/Aug/2021 17:57:42] "POST / HTTP/1.1" 200 -
INFO:root:POST request,
Path: /
Headers:
Host: 127.0.0.1:5001
User-Agent: Alertmanager/0.22.2
Content-Length: 781
Content-Type: application/json

Body:
{"receiver":"web\\.hook","status":"firing","alerts":[{"status":"firing","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"},"annotations":{"summary":"check2 alert summary"},"startsAt":"2021-08-22T06:47:54.913Z","endsAt":"0001-01-01T00:00:00Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","fingerprint":"c32443c5c37325c8"}],"groupLabels":{"alertname":"check2"},"commonLabels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"},"commonAnnotations":{"summary":"check2 alert summary"},"externalURL":"http://owner-desktop:9093","version":"4","groupKey":"{}:{alertname=\"check2\"}","truncatedAlerts":0}

127.0.0.1 - - [22/Aug/2021 17:58:35] "POST / HTTP/1.1" 200 -
```

## route

- Alertmanager はアラートを受け取ると、route の match を評価して処理を決定する
- 最上位の route からなるツリー構造を取っており、下位の route は親の route の設定を引き継ぎ、設定は子が上書き可能です
- continue が false の場合は、最初に一致した子ノードで処理が停止する
- continue が true の場合は、アラートは後続の兄弟ノードも評価される
- アラートが子ノードのどれとも一致しない場合は、現在のノードの構成パラメータによって処理される
- routes に子ノードを階層的に定義できる
- Alert のグルーピングはここで行う
  - グルーピングは label で行う

```
route:
  receiver: developers

  routes:
    - match:
        severity: warn
      receiver: admins
    - match:
        type: infra
      receiver: infras
```

## route の例

- group_by: ['alertname']
  - alertname label でグルーピングする
- group_wait: 30s
  - 初期アラート発生時から 30s 間で同一グループのアラートをまとめて送信する
- group_interval: 5m
  - 初期アラートを通知したあと、新しいアラートがグループに追加され、それを通知するまでの待機時間
  - 一般的には 5 分以上
- repeat_interval: 1h
  - すでに通知したアラートを再度通知するまでの待機時間
  - 一般的には 3 時間以上
- mute_time_intervals
  - mute にすべき時間を設定できる
  - root ではこれは設定できない
  - mute_time_intervals セクションの設定値と一致する必要がある

```
route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'web.hook'
```

## inhibit の例

- 同一のインスタンス、アラートが発生し、一方が critical、一方が warning の場合は warning は無視する
- target_matchers
  - mute されるアラートの一致条件
- source_matchers
  - mute の元(トリガー)となるアラートの一致条件
- equal
  - 同種のアラートであることを label により判定するための一致条件
  - inhibit を適用するには target と source で同一の label を持ってる必要がある

```
inhibit_rules:
- target_matchers: [ severity="warning" ]
  source_matchers: [ severity="critical" ]
  equal: ['alertname', 'instance']
```

## templates

- 通知の template

## 冗長化について

- API のポートは 9093
- 起動時オプションに --cluster を付けると冗長化できる
  - --cluster.peer=alert1.example.com:9094
  - クラスタの相互通信に使うポートは 9094
