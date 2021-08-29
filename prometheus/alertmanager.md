# Alertmanager

## 仕組み

- Prometheus は、定期的にルールを評価してアラートを生成してメトリクスとして保存し、Alertmanager にアラート情報を送信する
  - メトリクスが保存されるのはアラートが発生中の場合のみ
- アラートが正常化した後も、そのアラートが解決したことを知らせるため、15 分間は Alertmanager へアラート情報を送信する
- アラート情報には、startsAt, endsAt が含まれており、Alertmanager は、この endsAt によってアラートが発生中か、解決したかを判断する
  - Alertmanager は、endsAt が現時刻よりも前であればアラートが発生中、そうでなければ解決したと判断する
    - アラートはラベルによって同一かどうかを判断する
    - アラートは発生時も解決後も同じメッセージを送っており、endsAt のみが異なる
  - startsAt には、アラート開始時点の時刻が入る
    - Prometheus を冗長していた場合、それぞれが送るアラート情報の startsAt が異なるが、startsAt が過去のものが優先されてアラートが登録される
    - 通知が重複されて送られることはない
  - アラート発生中は、endsAt には、現時刻よりも 3 分後の時刻が入る
    - アラート情報は常に送られ続けるので、endsAt は常に更新続けられる
  - アラート解決後は、endsAt には、その解決時点の時刻が入る
- endsAt が現時刻よりも前のアラート情報を初めて受け取ったタイミングで、resolved のメッセージを通知する
  - メッセージが送られない場合でも、endsAt を経過したアラートは、アラート一覧から消える
  - endsAt を経過したアラートは、アラート一覧からは消える(この時即座には notify は飛ばない
  - その後、一定時間経過するか、endsAt を経過したアラートを受け取ったタイミングで resolved の notify が送信される

## Prometheus から Alertmanager へのリクエスト

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

アラートを発生させ、解決して一定時間経過するまでのリクエストの中身

```
# alert発生中
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:57:54.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:54:39] "POST /api/v2/alerts HTTP/1.1" 200 -

# alert発生中
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:59:09.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:55:09] "POST /api/v2/alerts HTTP/1.1" 200 -

# ここからalert解決後
[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:55:39] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:56:54] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:58:09] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 10:59:24] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:00:39] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:01:54] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:03:09] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:04:24] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:05:39] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:06:54] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:08:09] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:09:24] "POST /api/v2/alerts HTTP/1.1" 200 -

[{"annotations":{"summary":"check2 alert summary"},"endsAt":"2021-08-29T01:55:39.913Z","startsAt":"2021-08-29T01:53:54.913Z","generatorURL":"http://owner-desktop:9090/graph?g0.expr=check2%7Bjob%3D%22myjob%22%7D+%3E+0\u0026g0.tab=1","labels":{"alertname":"check2","instance":"localhost:9980","job":"myjob","output":"warningout","severity":"warning"}}]
127.0.0.1 - - [29/Aug/2021 11:10:39] "POST /api/v2/alerts HTTP/1.1" 200 -
```

## webhook

設定例

```
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'
```

以下のようなメッセージが通知される

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

- 細かい設定項目は以下を参照
  - https://github.com/prometheus/alertmanager#high-availability
- --cluster.peer=[target:port] を指定することでクラスタリングができる
- Alertmanager は、メモリ上に alerts、slicences, notificationLog を持っているが、これらのデータはプロセスがリスタートされると消失する
- クラスタリングをすることで、silences, nitificationLog は同期されるが、alerts は同期されない
  - アラート情報は Prometheus が定期的に送信してくるので問題ない
- Alertmanager は、すべてのアラート情報を受信するか、まったく受信しないことを想定とする
  - ロードバランサを間に入れてはいけない
  - データのバックアップ用のプロセスを立てておいて、そこにはいっさいアラート情報を転送しないというのはあり
