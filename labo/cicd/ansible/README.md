# ansible

- 公式ドキュメント
  - https://docs.ansible.com/ansible/latest/getting_started/index.html
- 事例
  - https://github.com/openstack/openstack-ansible

## 用語

- inventory
  - host の定義、vars の定義するためのもの
- playbooks
  - 実行の起点となるもの
  - playbook 事態に task を羅列するのではなく、roles 側そのタスクを定義をするのが一般的
- roles
  - tasks, vars, templates, files, などをコンポーネントとしてまとめたもの
  - role を使わなくても同じようなことは実現できるが、一般的なやり方として role にまとめるのがよい
- library
- test_plugins
- filter_plugins
- vars_plugins
- inventory_plugins
- lookup_plugins
- callback_plugins
- action_plugins
- handler
- Gathering Facts
  - 対象ホストの情報を ansible_facts 変数というものに格納する機能
  - playbook 実行時の初回に 1 度だけ実行される
  - なにを収集するかは、gather_facts を設定することで制御できる
