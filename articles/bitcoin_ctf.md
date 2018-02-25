# はじめに

Capture The Flag（CTF）とはセキュリティ系のコンテンストであり、いくつかの形式があるものの、ここではjeopardy形式と呼ばれるものについて説明する。jeopardy形式のCTFは暗号やバイナリ解析、フォレンジックといったジャンルごとに脆弱性を攻撃するなどして`FLAG{This_is_a_flag_word}`のような**フラッグワード**と呼ばれる文字列を得て、それを運営のサーバーへ送信して正しいかどうかを判定し、正しい場合にポイントが得られるという競技である。問題は一般的に5問から10問程度出題され、時間内により多くのポイントを獲得したチームが勝利となる。世界的に有名なCTFでは上位チームに賞金が与えられ、たとえば[CODE BLUE CTF 2017](http://ctf.codeblue.jp/)では1位のチームに賞金として30万円が送られたり、また[Google CTF 2017](https://capturetheflag.withgoogle.com/)では1位のチームに賞金として$13,337が送られたりなどがある[^google_ctf]。また、問題に対応するフラッグワードを運営に提出するための**スコアサーバー**と呼ばれるシステムがあり、これは他にも現在の問題の解答状況や順位を表示する機能があることが多い。
この記事ではBitcoinを利用した、著者の知る限りで新しいCTFの方法について述べる。

記事を読んで分からないことや質問、改善すべきところがある場合は気軽にコメントで教えてほしい。

[^google_ctf]: Google CTF 2017では2位、3位のチームにも賞金が送られている。

## 発表資料

この記事の内容について発表した際の資料を次のURLから入手できる。

- [アニメーションありPDF](https://y-yu.github.io/bitcoin-ctf-slide/bitcoin_ctf.pdf)
- [アニメーションなしPDF](https://y-yu.github.io/bitcoin-ctf-slide/bitcoin_ctf_without_animation.pdf)

なお、この発表資料は下記のGitHubリポジトリでソースコードを公開している。

- https://github.com/y-yu/bitcoin-ctf-slide

# Bitcoinを利用したCTFシステムの特徴

システムの詳細を述べる前に、提案するシステムの特徴を述べる。

- 正しいフラッグワードを提出した場合、参加者は直ちにその問題に対応する賞金が得られる
  - よって、従来のCTFではポイントの多い順に賞金決まるが、提案する方法では賞金が多い順に順位が決まる
- 賞金は全てBitcoinで支払われる
- 問題を最初に解答したチーム以外には賞金が支払われない
  - jeopardy形式のCTFは一般的に、問題に解答すれば解答した順番に関わらず一定のポイントを貰えるが、提案する方法では最初に解答すること以外に意味がない
- Bitcoinの性質により、問題を問いたチームに賞金が支払われることが明らかである

# Bitcoinを利用したCTFシステム

提案するCTFの詳細について述べる。

## CTF開始前の作業

1. 参加チーム$T_i$は運営に次を提出する（ただし$i$は$i$番目に参加登録をしたチームであることを示す$1$からはじまる連番のIDである）
  - チーム$T_i$のBitcoinの公開鍵$\mathcal{T}_i$
2. 運営は参加登録をCTFの当日より前に締め切る
3. 問題$j$に対応するフラッグワードを$F_j$として、またこの問題を解答した際に得られる賞金を$B_j$ BTCとする。運営は次のような`scriptPubKey`を持つ$B_j$ BTCのトランザクション$\mathrm{Tx}_j$を作成する（ただし$j$は$j$番目の問題を示す問題番号である）
  - $ans_{ij} := H\left(H(F_j \mid\mid i)\right)$であり、関数$H$はハッシュ関数[SHA256](https://ja.wikipedia.org/wiki/SHA-2)である[^midmid]

     ```math
\begin{array}{l}
\texttt{OP_DUP} \\
1 \\
\texttt{OP_EQUAL} \\
\texttt{OP_IF} \\
  \;\;\; \texttt{OP_DROP} \\
  \;\;\; \texttt{OP_SHA256} \\
  \;\;\; ans_{1j} \\
  \;\;\; \texttt{OP_EQUALVERIFY} \\
  \;\;\; \mathcal{T_1} \\
\texttt{OP_ELSE} \\
  \;\;\; \texttt{OP_DUP} \\
  \;\;\; 2 \\
  \;\;\; \texttt{OP_EQUAL} \\
  \;\;\; \texttt{OP_IF} \\
    \;\;\; \;\;\; \texttt{OP_DROP} \\
    \;\;\; \;\;\; \texttt{OP_SHA256} \\
    \;\;\; \;\;\; ans_{2j} \\
    \;\;\; \;\;\; \texttt{OP_EQUALVERIFY} \\
    \;\;\; \;\;\; \mathcal{T_2} \\
  \;\;\; \texttt{OP_ELSE} \\
    \;\;\; \;\;\; \texttt{OP_DUP} \\
    \;\;\; \;\;\; 3 \\
    \;\;\; \;\;\; \vdots \\
  \;\;\;\texttt{OP_ENDIF} \\
\texttt{OP_ENDIF} \\
\texttt{OP_CHECKSIG}
\end{array}
     ```
4. トランザクション$\mathrm{Tx}_j$を全てBitcoinのブロックチェーンへ送信する
  - ただし、トランザクションをブロックチェーンへ送信する時間はあらかじめ全参加チームに告知しておく必要がある
5. トランザクション$\mathrm{Tx}_j$のトランザクションIDをCTFの問題ページに記載する

[^midmid]: “$\mid\mid$”はデータの連結を示す。

## CTF開始中の作業

ここではCTFを開始した後に、チーム$T_i$が問題$j$のフラッグワード$F_j$を得た場合について考える。

1. チーム$T_i$はトランザクション$\mathrm{Tx}\_{j}$を入力に持ち、次のような`scriptSig`を持つトランザクション$\mathrm{Tx}_{ij}$を作成する
  - ただし$h_{ij} := H(F_j \mid\mid i)$であり、$S_i$はチーム$T_i$の公開鍵$\mathcal{T}_i$に対応する秘密鍵によって作成された署名である

    ```math
\begin{array}{l}
S_i \\
h_{ij} \\
i
\end{array}
    ```
2. チーム$T_i$はトランザクション$\mathrm{Tx}_{ij}$をBitcoinのブロックチェーンへ送信する
3. もし問題$j$がまだ解かれていないかつフラッグワードが正しい場合、チーム$T_i$は$B_j$ BTCを獲得する

## CTF終了後の作業

1. 運営はBitcoinのブロックチェーンをダウンロードする
2. チームに対応するBitcoinの公開鍵を用いて問題を解答することで獲得したBitcoinの量を計測する
3. Bitcoinを獲得した量で順位付けを行う

# FAQ

## なぜフラッグワードを直接ブロックチェーンに提出しないのか？

このプロトコルでは$ans_{ij} := H\left(H(F_j \mid\mid i)\right)$と比較する方法でフラッグワードの検証を行っているが、ブロックチェーンに直接フラッグワードを提出すればよりシンプルになると思われるかもしれない。ところが、Bitcoinのブロックチェーンに送信されたトランザクションはブロックに入るまでに時間がかかるため、他の参加者が未処理トランザクションのキューを監視してフラッグワードをコピーするような攻撃が可能になる。それを防ぐためにこのような方法を採用した。

## 参加者はBitcoinが必要ではないか？

参加者はトランザクションを送信するための手数料が必要になる。

## 解かれなかった問題の賞金を回収できるのか？

$\texttt{OP_IF}$を追加して、運営の公開鍵であればCTF終了後に賞金を取り出せる、という処理を入れることができる。ただし、運営がCTF中にBitcoinを取り消すことができないように$\texttt{OP_CHECKLOCKTIMEVERIFY}$を利用するため、通常の時間でぴったり開始・終了することができないと考えられる。このため提案手法を用いたCTFは、開始時刻をBitcoinのブロックチェーンの長さが$n$に達した時とし、終了時刻をブロックチェーンの長さが$n + m \; (m > 0)$に達した時としておくとよいだろう。

## 問題が解かれたといつ判定するのか？

著者の考えでは、フラッグワードのハッシュ値が入ったトランザクションを含むブロックから3ブロック伸びた時点で確定としてよいと思われる。Bitcoinのブロックチェーンは約10分で1ブロック作られるので、完全に確定するまで30分かかるということになる。ただ、場合によってはブロックに入った時点で確定させるということもできる。

## 参加者はBitcoinのブロックチェーンを監視する必要がある？

参加者は、問題$j$と対応するトランザクション$\mathrm{Tx}_j$がまだ誰の手にも渡っていないことを確認しつづける必要がある。よって、参加者はBitcoinのブロックチェーンを監視しなければならない。

## なぜ問題に対応するトランザクションをブロックチェーンへ送信する時間を公開する必要があるのか？

提案するCTFのシステムは、あるハッシュ値の原像[^preimage]を知っていれば得点できるものである。つまり、ハッシュ値の原像を総当たりで探索することで問題を解かなくとも得点できてしまう。原像の総当たり的な探索を規制することはできないので、全ての参加者が公平に不正ができるように公開する時間を明らかにする必要がある。一方でこのプロトコルではハッシュ関数にSHA256を利用するため、総当たりで原像を求めることは極めて困難であると考えられる。従って、このことはそれほど重要に考える必要はないだろう。

## この方法は直ちに実行できるのか？

現在のBitcoinでは、提案する方法に用いられるような`scriptPubKey`や`scriptSig`を持つようなトランザクションを非標準としており、リファレンス実装においてはBitcoinのネットワークへ拡散したりマイニングを実行しない。従って、可能ではあるものの、現実的にはマイナーの多くがリファレンス実装に従っているであろうから、現時点ではこの方法は難しいと思われる。ただ手数料を多めに払った場合、マイナーはリファレンス実装を無視する可能性がある。また、Bitcoinではなく[Ethereum](https://www.ethereum.org/)といったより汎用的なブロックチェーンを利用することで、実現できると思われる。

[^preimage]: ハッシュ値の原像とは、ハッシュ値$H(x)$に対する$x$のことである。

### 追記（2018/1/3）

@lotz さんがEthereumのスクリプトであるSolidityで実装してくださいましたので、そちらも参考になると思われます。

- [Solidityで作るCapture The Flag](http://lotz84.hatenablog.com/entry/2018/01/02/134056)

# まとめ

このように、Bitcoinのシステムを利用したCTFのシステムを作成した。もし著者がCTFを運営することになったらこの方法でやってみたい。

# 参考文献

- [Script (Bitcoin Wiki)](https://en.bitcoin.it/wiki/Script)