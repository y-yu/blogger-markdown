# 続編

この記事で指摘した課題を解決した新しいガチャをつくりました。

[コミットメントを用いた公平なガチャシステム](http://qiita.com/yyu/items/fce9b33c784e0631ddf6)

# はじめに

[僕が（ほとんどを）考えた公平なガチャシステム](http://qiita.com/yyu/items/90db09c57514758bd68c)を[todesking](https://twitter.com/todesking)さんにとりあげていただいた。

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr">安全ガチャだ <a href="https://t.co/0wQZ5WzwjT">https://t.co/0wQZ5WzwjT</a></p>&mdash; トデス子&#39;\ (@todesking) <a href="https://twitter.com/todesking/status/683547727406313472">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

そうしたところ、[mala](https://twitter.com/bulkneets)さんが次のようなガチャシステムを考えてくださった。

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr"><a href="https://twitter.com/todesking">@todesking</a> ものすごく単純化した。ハッシュ云々とかイランと思う <a href="https://t.co/A2U1G8Re8a">https://t.co/A2U1G8Re8a</a></p>&mdash; mala (@bulkneets) <a href="https://twitter.com/bulkneets/status/683574254315507712">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

これを僕も読んでみて、考えられる限り色々考えてみた結果をここにまとめる。

# malaさんのガチャシステム

malaさんが考えたガチャシステムの全文は次のGistにアップロードされている。

> https://gist.github.com/mala/f33c9654af5e06e8bca9

## プロトコル

上記の文章を僕なりに説明すると次のようになる。

1. 運営は、$n$種類のカード$K_1 \dots K_n$に番号を割り当てる

    |  カード |   番号   |
    |:-------:|:--------:|
    |  $K_1$  |    $1$   |
    |  $K_2$  |    $2$   |
    | $\vdots$ | $\vdots$ |
    |  $K_n$  |    $n$   |
2. 運営は割り当てた番号をシャッフルし、シャッフルした結果をユーザーへ公開する
3. 運営は**キー**と呼ばれる数値を用意する（ただし、キーは$n$より小さい）
4. 運営はキーを[対称鍵暗号](https://ja.wikipedia.org/wiki/%E5%85%B1%E9%80%9A%E9%8D%B5%E6%9A%97%E5%8F%B7)で暗号化してユーザーへ送信する
5. ユーザーは暗号化されたキーを受けとり、(2)でシャッフルされた番号の中から一枚を選択する
6. 運営はキーを暗号化する際に用いた対称鍵をユーザーに公開する
7. ユーザーは暗号化されたキーを復号し、選択した番号にその数を足して$n$で割った剰余を求める
8. ユーザーは(7)で求めた剰余に対応するカードを得る

この方法で大丈夫なのかどうかについて議論を進めていく。

# 改良案

これを聞いて僕が考えたところ、改良点を思いついたのでそれについて説明する。

## マリシャスな運営による不公平な暗号鍵の送信

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr"><a href="https://twitter.com/_yyu_">@_yyu_</a> <a href="https://twitter.com/todesking">@todesking</a> 暗号化データから複数の復号結果が得られうるようなアルゴリズムだとサーバー側で運営者にのみ有利な結果が選択されるような(レア度が低い) 別の鍵を作れますね。よく知られてるアルゴリズム使うだけで十分なのでは、と思ってその辺りは端折りました</p>&mdash; mala (@bulkneets) <a href="https://twitter.com/bulkneets/status/683625361653907456">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

malaさんが仰るように、キーを暗号化する際に用いた秘密鍵と全然関係のないデータを運営はさも対称鍵であるかのように偽ってユーザーへ公表する可能性がある。こうした可能性を排除するために、[ゼロ知識証明](https://ja.wikipedia.org/wiki/%E3%82%BC%E3%83%AD%E7%9F%A5%E8%AD%98%E8%A8%BC%E6%98%8E)を用いるなどして、**暗号化の際に用いた対称鍵と公開した秘密鍵が同じであること**をユーザーに対して証明する手続きが必要であると思われる。

# まとめ

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr">確率操作されてるって騒ぐ層にも理解できるアルゴリズムであることが必要だと思う</p>&mdash; mala (@bulkneets) <a href="https://twitter.com/bulkneets/status/683580099212349440">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

malaさんの言い方はややキツいが、僕の考えたアルゴリズムはやや複雑すぎたと思うところはある。一方でmalaさんのガチャシステムは非常に簡潔でよいと思う。また、malaさんやtodeskingさんには、公平なガチャシステムに関する議論に参加していただけたことに大変感謝している。


# P.S

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr">ユーザが運営をまったく信頼しないことを前提とする公平性証明ガチャを導入したところで、ガチャ以外のロジックの妥当性が問題になるだけだし思いやりと信頼でやっていくほうがマシなのではという気もしてきた……</p>&mdash; トデス子&#39;\ (@todesking) <a href="https://twitter.com/todesking/status/683557660973645828">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

<blockquote class="twitter-tweet" lang="ja"><p lang="ja" dir="ltr">ガチャ以外にも、ソーシャルゲームのありとあらゆる確率が絡む局面を秘密計算で実装すれば、ユーザーはアプリケーションをリバースエンジニアリングして公平性を確かめることができる。</p>&mdash; 吉村 優 (@_yyu_) <a href="https://twitter.com/_yyu_/status/683664323051311104">2016, 1月 3</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

