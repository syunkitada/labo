# controller runtime

クライアントを作成するためにはまず Scheme を用意する必要があります。
Scheme は Go の struct と GroupVersionKind を相互に変換したり、異なるバージョン間での Scheme の変換をおこなったりするための機能です。

## クライアントのキャッシュ機構

- クライアントは最初にまとめてリソースを取得してキャッシュし、そのあとは watch してキャッシュを更新します
  - watch しすぎて k8s がダウンするというのを聞いたことがあるが、watch の処理コストはどのくらいだろうか？
- コントローラは k8sAPI を直接 GET することはありません
  - 直接 GET することもできます

## Reconcile の実行タイミング

- コントローラーの扱うリソースが作成、更新、削除されたとき
- Reconcile に失敗してリクエストが再度キューに積まれたとき
- コントローラーの起動時
- 外部イベントが発生したとき
- キャッシュを再同期するとき(デフォルトでは 10 時間に 1 回)
- Reconcile 処理はデフォルトでは 1 秒間に 10 回以上実行されないように制限されている
- これらのイベントが高い頻度で発生する場合は、Reconciliation Loop を並列実行するように設定可能です。

## 削除処理

- ownerReference
  - 親リソースが削除されると、そのリソースの子リソースもガベージコレクションにより自動的に削除される仕組みです。
  - k8s ではリソースの親子関係を表すために、.metadata.ownerReferences を持っている
  - controller-runtime が提供している controllerutil.SetControllerReference 関数を利用することで、指定したリソースに ownerReference を設定することができます。
- controllerutil.SetOwnerReference

  - 1 つのリソースに 1 つのオーナーのみしか指定できず、controller フィールドと blockOwnerDeletion フィールドに true が指定されているため子リソースが削除されるまで親リソースの削除がブロックされます。 一方の SetOwnerReference は 1 つのリソースに複数のオーナーを指定でき、子リソースの削除はブロックされません。

- Finalizer
  - ownerReference とガベージコレクションにより、親リソースと一緒に子リソースを削除できると説明しました。 しかし、この仕組だけでは削除できないケースもあります。 例えば、親リソースと異なる namespace やスコープの子リソースを削除したい場合や、Kubernetes で管理していない外部のリソースを削除したい場合 などは、ガベージコレクション機能は利用できません。
- finalizers フィールドが付与されているリソースは、リソースを削除しようとしても削除されません。
- 代わりに、deletionTimestamp が付与されるだけです。
- カスタムコントローラーは deletionTimestamp が付与されていることを発見すると、そのリソースに関連するリソースを削除し、その後に finalizers フィールドを削除します。 finalizers フィールドが空になると、Kubernetes がこのリソースを完全に削除します。
  関数として controllerutil.ContainsFinalizer、controllerutil.AddFinalizer、controllerutil.RemoveFinalizer などを提供しているのでこれを利用しましょう。
