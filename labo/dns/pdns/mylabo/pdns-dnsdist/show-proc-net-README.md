# show-proc-net.py

`/proc/net/tcp`と`/proc/net/udp`をパースして、人が読みやすい形式でネットワーク接続を表示する Python スクリプトです。

## 機能

- TCP/UDP 接続の情報を読みやすい表形式で表示
- IPv4 と IPv6 の両方に対応
- 接続状態の表示（LISTEN, ESTABLISHED, TIME_WAIT 等）
- UID、送受信キュー情報の表示
- 柔軟なフィルタリングオプション

## 使用方法

### 基本的な使用方法

```bash
# すべてのリスニングソケットを表示（TCP/UDP）
./show-proc-net.py

# すべての接続を表示（確立済み接続も含む）
./show-proc-net.py -a

# LISTEN状態の接続のみ表示
./show-proc-net.py -l

# TCP接続のみ表示
./show-proc-net.py -t

# UDP接続のみ表示
./show-proc-net.py -u

# IPv4接続のみ表示
./show-proc-net.py -4

# IPv6接続のみ表示
./show-proc-net.py -6

# TCP IPv4のリスニングポートのみ表示
./show-proc-net.py -t -4

# LISTEN状態のTCP接続のみ表示
./show-proc-net.py -l -t
```

### オプション

- `-a, --all`: すべての接続を表示（リスニングだけでなく確立済み接続も含む）
- `-l, --listen`: LISTEN 状態の接続のみ表示
- `-t, --tcp`: TCP 接続のみ表示
- `-u, --udp`: UDP 接続のみ表示
- `-4, --ipv4`: IPv4 接続のみ表示
- `-6, --ipv6`: IPv6 接続のみ表示
- `-h, --help`: ヘルプメッセージを表示

## 出力形式

```
====================================================================================================
TCP Connections:
====================================================================================================
Local Address                  Remote Address                 State           UID      Queues
----------------------------------------------------------------------------------------------------
127.0.0.54:53                  *:*                            LISTEN          101      TX:0 RX:0
*:22                           *:*                            LISTEN          0        TX:0 RX:0
```

### 表示される情報

- **Local Address**: ローカルアドレスとポート
- **Remote Address**: リモートアドレスとポート（`*:*`はすべてのアドレス）
- **State**: 接続状態
  - `LISTEN`: リスニング状態
  - `ESTABLISHED`: 確立済み
  - `TIME_WAIT`: TIME_WAIT 状態
  - `CLOSE`: クローズ状態（主に UDP）
  - その他の TCP 状態
- **UID**: プロセスのユーザー ID
- **Queues**: 送信（TX）・受信（RX）キューのバイト数

## /proc/net ファイルフォーマット

このスクリプトは以下のファイルをパースします：

- `/proc/net/tcp`: IPv4 TCP 接続
- `/proc/net/tcp6`: IPv6 TCP 接続
- `/proc/net/udp`: IPv4 UDP 接続
- `/proc/net/udp6`: IPv6 UDP 接続

各行のフォーマット（スペース区切り）：

1. スロット番号
2. ローカルアドレス:ポート（16 進数）
3. リモートアドレス:ポート（16 進数）
4. 状態（16 進数）
5. TX:RX キュー（16 進数）
6. タイマー情報
7. 再送回数
8. UID
9. タイムアウト
10. Inode 番号

## 実装の詳細

### 16 進数 IP アドレスの変換

`/proc/net`ファイルでは、IP アドレスがリトルエンディアンの 16 進数形式で格納されています。

例：

- IPv4: `0100007F` → `127.0.0.1` (バイト順を逆転)
- IPv6: 32 文字の 16 進数 → 標準的な IPv6 表記

### TCP 状態コード

- `01`: ESTABLISHED
- `02`: SYN_SENT
- `03`: SYN_RECV
- `04`: FIN_WAIT1
- `05`: FIN_WAIT2
- `06`: TIME_WAIT
- `07`: CLOSE
- `08`: CLOSE_WAIT
- `09`: LAST_ACK
- `0A`: LISTEN
- `0B`: CLOSING

## 使用例

### DNS 関連のポートを確認

```bash
./show-proc-net.py | grep ":53"
```

### 特定のポートがリスニングしているか確認

```bash
./show-proc-net.py -t | grep ":22"
```

### すべての ESTABLISHED 接続を確認

```bash
./show-proc-net.py -a | grep ESTABLISHED
```

## 注意事項

- `/proc/net`ファイルへの読み取り権限が必要です
- 通常は一般ユーザーでも実行可能ですが、一部の情報は制限される場合があります
- UID は数値で表示されます（ユーザー名への変換は行っていません）
