# Note

## hash_behaviour = replace(default) vs merge

- 辞書型の変数を上書きする場合の挙動について
- 以下で少し議論がされている
  - https://github.com/ansible/ansible/issues/73089
- 以下で merge を作った人が後悔したと言っているが、merge の具体的にどこがダメなのかが指摘されてない
  - https://www.reddit.com/r/ansible/comments/a7x92q/comment/ec8mf7f/
- 基本的に merge はバグの原因になるので replace のがよいらしい?

- 考え方
  - 複雑で深すぎるデータ構造は使わないこと
  - 何かをオーバライドしたいときは再定義すること
  - 変数の優先順位は複雑にすべきではない
  - シンプルに保つこと

## roleの依存関係について

role間の依存関係は、以下のようにmeta/main.ymlに定義することができる。

meta/main.yml

```
dependencies:
  - role: hoge
```

これが定義されていると、roleが実行されるときに、その直前に依存roleが実行されます。

また、依存roleの実行は、他のroleで同じ依存roleが実行済みだったとしても改めて実行されます。

roleから他のroleのタスクを実行する手段として、import_role, include_roleモジュールを利用する方法もあるが、基本的にはmeta/main.ymlに書き込むことが推奨される。

最後に、roleの依存はデプロイロジックの複雑化につながるので、なるべく依存はせずにデプロイロジックはrole内で閉じるほうが望ましい。
