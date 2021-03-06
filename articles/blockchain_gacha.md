
# はじめに

この記事は[第2のドワンゴ Advent Calendar 2017](https://qiita.com/advent-calendar/2017/dwango2)の9日目の記事である。

2015年からはじめた**公平なガチャ**という研究テーマは、“コミットメント”といった暗号技術を利用する方針で研究が進んだ。一方でコミットメントではなくブロックチェーンを利用した公平なガチャを実装しようという研究が[SCIS 2017](http://www.iwsec.org/scis/2017/)で佐古さんらによって提案された。また[CSS 2017](http://www.iwsec.org/css/2017/)において江原さんらはEthereumを利用した方法を提案した。この記事ではこれまでのコミットメントを利用した公平なガチャについておさらいしつ、江原さんらの論文に基づくブロックチェーンによる公平なガチャについて説明する。
なお、もしこの文章に間違いなどがあったとしてもそれは記事を書いた筆者の落ち度であり、上記の論文の著者らは無関係である。もし間違いを見つけたり、あるいは疑問がある場合は気軽にコメントで報告してほしい。

# 公平なガチャとは？

従来のソーシャルゲームなどに実装されたガチャは、あらかじめ運営からSSRなどのレアリティに基づいた景品の出現確率が公表されているが、それはあくまで運営が公表した値でしかなく、本当にその通りなのか疑う余地がある。従来のガチャは確率の計算がサーバーサイドアプリケーションで行われるため、ユーザーがリバースエンジニアリングなどを行ってもガチャの公平性をたしかめることができない。公平なガチャとは、ユーザーにとっても運営にとってもガチャによる景品の出現確率が実装に基づいて明らかなガチャである。

# コミットメントによる公平なガチャ

まずは私がかつてから考えていたコミットメントによる公平なガチャについて述べる。まずはコミットメントという暗号技術について説明し、ハッシュ関数を使ったコミットメントの具体的な実装方法を紹介する。そしてコミットメントの実装によって生じる**隠蔽**と**束縛**のトレードオフを述べ、このトレードオフが公平なガチャにもたらす影響を紹介する。最後に**否認**を利用した不正を紹介し、それによるコミットメントによる公平なガチャの課題をあきらかにする。

## コミットメント

コミットメントとは暗号技術のひとつであり、2つの操作**コミット**と**公開**から成り立つ。

<dl>
  <dt>コミット</dt>
  <dd>送信者はコミットしたい情報$b$を暗号化した暗号文$c$を受信者へ送信する</dd>
  <dt>公開</dt>
  <dd>送信者は受信者が暗号文$c$から情報$b$を復元できるように付加的な情報$r$を受信者に送信する</dd>
</dl>

そして、この二つの操作には次のようなことが言える。

<dl>
  <dt>隠蔽</dt>
  <dd>コミットのステップでは、受信者はコミットされた値$c$から情報$b$についてなにも分からない</dd>
  <dt>束縛</dt>
  <dd>送信者は受信者へ暗号文$c$を送信した後、コミットした値$b$を変更することができない</dd>
</dl>

コミットメントはハッシュ関数を利用することで簡単に構成することができる。

## ハッシュ関数を用いたコミットメントによるガチャ

ハッシュ関数を用いてどのようにコミットメントを構成するのかについて述べる。ここではアリスをガチャの運営とし、ボブをガチャのユーザーとする。アリスとボブは出力が$2n$ビットのハッシュ関数$H$を用意しているものとする。また、アリスがボブに対してメッセージ$m \in \\{0,1,\dots,2^n - 1\\}$をコミットメントしたいものとすると、プロトコルは次のようになる。

1. アリスは$n$ビットの長さを持つ乱数$r$を生成する[^mid]
2. アリスはボブに$c := H(m \mid\mid r)$を送信する[^midmid]。ただし$\left|m \mid\mid r\right| = 2n$である
3. ボブはアリスに乱数$n$を送信する
4. アリスはボブに$n + m$と対応する景品を送信し、また$m$と$r$をボブへ公開する
5. ボブは$c = H(m \mid\mid r)$を検証する

[^mid]: $|m|$はメッセージ$m$のビット長を表す。
[^midmid]: $\mid\mid$はビット列の連結を表す。つまり$a \mid\mid b$は$a$と$b$の連結である。

まず、(2)でアリスがボブへ$c$を送信したあとに、なにか適当な$m' \in \\{0,1,\dots,2^n − 1\\}$に変更することはできないかについて考える。(5)でボブが検証するため、アリスは次を満す$r'$を探索する必要がある。

$$
c = H(m' \mid\mid r')
$$

このような$r'$は、ハッシュ関数$H$の性質から$n$ビットでは不可能である。よって、アリスはどれだけ努力をしたとしても$c$をボブへ送信した後になって$m$を変更することはできない。もし変更した場合(5)の検証によって変更したことがボブに知られてしまう。

## 隠蔽と束縛

さて、さきほど述べハッシュ関数を用いたコミットメントにおいて、ボブはアリスから送信された$c$を用いて$m$を復元することはできないかについて考える。$c = H(m \mid\mid r)$となる$m$と$r$が一意であることから、ボブは総当たり的に$2n$ビットのデータをハッシュ関数$H$へ投入して$c$と比較することで、いずれは$m$と$r$を特定することができる。しかし、ハッシュ関数の性質から、$c$のようなハッシュ値からその原像[^preimage]を求めることは困難であるため、ボブは総当たりより効率的な探索がない。
ハッシュ関数を利用したコミットメントについて整理すると、アリスはどれだけ努力をしても$m$を変更するという、束縛に対する攻撃ができないが、一方でボブは$c$から$m$を特定するという隠蔽に対する攻撃が可能である。ただし、隠蔽に対する攻撃が成功するためには巨大な計算能力が必要であるためこれは安全である。このことから、アリスはたとえ巨大な計算能力があったとしても不正ができないが、ボブは巨大な計算能力があれば不正ができるという点でボブに有利なプロトコルである。
すると、隠蔽も束縛も両方ともが計算能力に依存しない完全なものであってほしいが、残念なことに隠蔽も束縛も完全なコミットメントは存在しない[^no_such_commitment]。
では、ハッシュ関数によるコミットメントとは逆に、束縛が計算能力に依存しており隠蔽が完全であるコミットメントをガチャに利用したとする。ユーザーであるボブは隠蔽が完全であるため、$c$のようなコミットされた値から情報を得ることはできない。一方でアリスは巨大な計算能力があれば、ボブの送信した値を見た後で$m$から$m'$のように元の値を変更することができる。つまり、このガチャは次のような性質がある。

[^preimage]: ハッシュ値$h := H(x)$における$x$のことを、$h$の原像と言う。
[^no_such_commitment]: このことはこのような両方が完全なコミットメントを仮定すると矛盾が発生するという背理法で証明できる。

<dl>
  <dt>隠蔽が計算量に依存している場合</dt>
  <dd>隠蔽が計算の複雑さに依存しているので、ユーザーは計算資源を投入すればコミットメントから元のメッセージを復元することができる。よってユーザーが有利である</dd>
  <dt>束縛が計算量に依存している場合</dt>
  <dd>一方で束縛が計算の複雑さに依存しているので、運営が莫大な計算資源を投入すればコミット後に値を変更できる。よって運営が有利である</dd>
</dl>

つまり、コミットメントを利用したとしても完全に公平ではない。

## 否認と署名における鍵配布機関

コミットメントに対する別の攻撃として、次のようなものが考えられる。

- ボブがアリスが発行したものではない偽のコミット（$c$）を捏造する
- アリスが、ボブのコミットは発行していないと嘘をつく

このような問題は**署名**によって解決することができる。電子署名には次の二つの鍵が必要である。

<dl>
  <dt>秘密鍵</dt>
  <dd>署名をするために使う鍵であり、これは署名者のみが知る</dd>
  <dt>公開鍵</dt>
  <dd>署名を検証するために使う鍵であり、これは多くの検証者が知る</dd>
</dl>

つまり、コミット$c$にアリスが自身の秘密鍵で署名をし、ボブがアリスの公開鍵でそれを検証することでこの問題を解決できる。ところが、アリスの公開鍵は誰がボブへ届けるとよいのかという問題が発生する。たとえばアリスのWebサイトなどで公開した場合、アリスは都合が悪くなったときに公開鍵を変更する可能性がある。従って、どこか信頼のおける第三者に公開鍵を配布してもらう必要があるが、そもそもそのような信頼できる第三者がいるのであれば、その第三者が乱数を生成すればよい。ただ、たとえばSSL/TLSの証明書[^certificate]をこのガチャに転用するといったことも可能と思われるので、乱数を生成する第三者よりは簡単に見つけられると思われる。

[^certificate]: 証明書は認証局の署名がなされた公開鍵である。認証局の公開鍵はブラウザやOSにインストールされている。

## コミットメントによる公平なガチャのまとめ

これまでの議論から、コミットメントによる公平なガチャは次のような欠点を持っている。

- 利用するコミットメントが完全な隠蔽を持つか、あるいは完全な束縛を持つかによって厳密には運営とユーザーの間に不公平が生れる
- コミットを否認したり捏造したりする攻撃の対策に署名を導入したいが、公平な鍵配布機関が必要となる

また検証可能乱数という暗号技術もあるが、こちらも乱数の検証に公開鍵のような仕組みを用いるため、鍵配布問題に直面する。

# ブロックチェーンによる公平なガチャ

コミットメントを利用した公平なガチャの説明の前に、まずはEthereumがブロックチェーンをどのように利用しているのかを述べる。そしてEthereumを利用した公平なガチャを説明する。

## Ethereum

EthereumはBitcoinのような単なる暗号通貨とは異なり、単なる通貨の取引だけではなくマイナーにプログラムを実行してもらうことができる。Bitcoinにも_Script_というスタックマシーンベースのプログラムを入力できるが、BitcoinのScriptは非チューリング完全であったり、リファレンス実装は送金の命令以外を受理しないといった制約がある。一方でEthereumの上ではより汎用的なプログラムをマイナーに実行させ、その結果をブロックチェーンに記録することができる。そのとき、プログラムの量と1命令あたりの料金から最終的なプログラムの実行料金がマイナーに提供されるという仕組みとなっている。

## ブロックチェーンによる公平なガチャ

ブロックチェーンによる公平なガチャは次のように実装する。まず、ガチャの運営アリスとアリスのガチャを引くユーザーであるボブがいるものとし、ボブのアドレスを$\mathcal{B}$とする。また関数$H$を適切なハッシュ関数であるとし、次のようにする。

1. ボブは乱数$r_B$を生成する
2. ボブはマイナーに次のような命令を持つトランザクションを送信する。ただしこのトランザクションには乱数$r_B$が含まれている
    1. マイナーはトランザクションを実行するごとに一意な番号$n$を生成する
    2. マイナーは組$(n, r_B)$をブロックチェーンに書き込む
3. アリスはブロックチェーンから$n$を読み取り、$n$に対応する乱数$r_A$を生成する。
4. アリスはマイナーに次のような命令持つトランザクションを送信する。ただしこのトランザクションには乱数$r_A$が含まれている
    1. このときのブロックチェーンの長さを$i$として、組$(r_A, i)$をブロックチェーンに書き込む
5. $i + 1$ブロックのハッシュ値を$h$として、アリスは$\alpha := H\left(r_A \mid\mid r_B \mid\mid n \mid\mid \mathcal{B} \mid\mid h\right)$を計算し、それに対応する景品をボブに与える
    - ただし、このときの値と景品の対応をボブは事前に知っているものとする
6. ボブは$\alpha = H\left(r_A \mid\mid r_B \mid\mid n \mid\mid \mathcal{B} \mid\mid h\right)$を検証する

コミットメントを利用する公平なガチャは景品に対応する値の計算に、アリスとボブの乱数を両方利用することで公平にしていたが、それゆえにハッシュ関数などを用いてコミットメントをする必要があった。一方でブロックチェーンを利用する公平なガチャは景品に対応する値の計算にアリスとボブの乱数と、さらにブロックチェーンのブロックのハッシュ値を利用している。ブロックのハッシュ値は**ノンス**と呼ばれる値とブロックのデータをハッシュ関数に投入し、その結果となるハッシュ値がある値より少なくなければならない。ノンスはマイナーの計算能力で総当たり的に求める他ないため、その結果であるブロックのハッシュ値を予測することは困難である。このようなブロックのハッシュ値を景品の計算に利用することで、コミットメントといった暗号技術を省くことができる。

## 計算の費用

ブロックチェーンへトランザクションを投入するためには手数料が必要となる。江原さんらの論文によれば、当時のレートで計算のたびに約1 USDの費用が必要であった。当時の1 ETH = 323 USDであったと記述されているが、現在は1 ETH = 506 USDであるから計算のたびに約1.6 USDが必要となる。ガチャのたびに1.6 USDを支払うのは効率が悪いため、たとえばメルセンヌ・ツイスタといった疑似乱数生成関数を用意しておいて、上述のプロトコルで得られた値を疑似乱数生成関数に投入することで、使い回すという手法が考えられる。

# まとめ

公平なガチャについて長く議論してきたが、ブロックチェーンを利用する方法が現在の技術では最も公平ではないかというのが筆者の見解である。さらなる改良をするとしたら、次の点が考えられる。

1. メルセンヌ・ツイスタなどを利用してブロックチェーンへのトランザクション量を削減する
2. 有限回の試行で必ず特定の景品が獲得できる方式も実装する

まず(1)は上述したようにブロックチェーンへのトランザクションには料金がかかってしまうので、なるべく少なくする方がよい。上記のプロトコルで生成した乱数をシードとして、メルセンヌ・ツイスタのような疑似乱数生成関数を利用することで解決できると考えられる。また(2)については、このような有限回の試行で必ず特定の景品を獲得できるガチャのことを**ラスベガスではないガチャ**と言う[^LasVegas]。ラスベガスではないガチャは[マークルツリー](https://ja.wikipedia.org/wiki/%E3%83%8F%E3%83%83%E3%82%B7%E3%83%A5%E6%9C%A8)を用いることで実装できると筆者は考えているが、きちんとしたプロトコルをまだ考えていないので、こちらも考える余地があると思われる。

最後に、このような透明性を持ったガチャを実装するゲームが今後増えて欲しいと思う。

[^LasVegas]: 逆に、今まで我々が議論してきたガチャは**ラスベガスなガチャ**であり、これは有限回の試行で必ず景品が得られるとは限らないガチャである。たとえば「確率が1%のガチャ」は運によっては手に入らないかもしれないためラスベガスなガチャであり、「確率が1%だがトータルで7万円を課金すると任意の景品を選んで獲得できるガチャ」はラスベガスではないガチャである。

# 参考文献

- ブロックチェーンによる乱数生成の透明性確保（江原 友登, 多田 充）
- [公平なガチャシステムのまとめ](https://qiita.com/yyu/items/ffa5960a721a0b36a354)
