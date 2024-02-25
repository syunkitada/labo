# Tips

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
