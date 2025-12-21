## MySQL: Tips

### max_connections はどのくらいに設定すべきか？

max_connections は、mysql server が接続可能な最大のコネクション数の設定値です。

一口にコネクションと言っても active なものもあれば、idle なものもあり、max_connections はその総量を制限するための設定値です。

active コネクションはある程度のサーバリソースを使うので気にする必要があるのですが、idle コネクションは CPU はほぼ消費せずメモリをわずかに消費する程度です。

例えば、idle コネクションが 10000 だったとしても CPU 消費はほぼなく、メモリを 2GB 程度消費する程度である。

このため、idle コネクションの数はあまり制限する必要はありません。

もし、クライアントサイドで connection pooling を行っている場合、コネクションのほとんどは idle である場合が多く、max_connections による制限はほとんど意味をなしません。

なので、雑に 2000 と設定しても問題ありません。メモリに余裕があるなら 10000 と設定しても良いと思います。

参考

- [mita2 database life: MySQL max_connections は雑に設定しておけば良い](https://mita2db.hateblo.jp/entry/2020/05/31/175523)

### connection pooling について

connection pooling は、クライアントサイドで一度確立したコネクションを一定数プールして使い回すための仕組みです。

これを利用することで、TCP 接続や認証などの新規接続処理をスキップすることができます。

ただ、接続処理部分以外に占める時間やリソースのほうが圧倒的に割合が多く、connection pooling を利用することはそこまで重要ではありません。

- [mita2 database life: MySQL Connection Pooling と Persistent Connections はチョット違うという話](https://mita2db.hateblo.jp/entry/2020/08/02/162024)

#### client side: max pool size はどのくらいに設定すべきか？

＊ 設定名は、クライアント実装によって変わります。

普段の active コネクション数程度は pooling して再利用するようにしておくと良いと思います。

#### client side: max connection lifetime はどのくらいに設定すべきか？

＊ 設定名は、クライアント実装によって変わります。

プールしたコネクションを何秒維持するかの値です。

コネクションは長時間持ち続けないほうが良いため、長くても 50 秒程度にしておくと良いと思います。

これは、DB の冗長化が LB や DNS などで行われていることが多く、メンテナンスなどで DB ノードの切り替わりが発生したりすると、古いコネクションが利用できなくなる場合があるためです。

#### client side: max connection (max open connections) はどのくらいに設定すべきか？

＊ 設定名は、クライアント実装によって変わります。

mysql 側でも max_connections という設定値で最大接続数は管理されますが、クライアントサイドでもスパイク時などに mysql へ不用意にコネクションを貼らないようにハードリミットを設けると良いと思います。

定常的なコネクション数の 3 倍程度はあると良いかなと思いますが、この辺は適宜調整かと思います。
