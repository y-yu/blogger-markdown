_公平な第三者なしにプレイヤーの情報秘密を保つMental Pokerのプロトコル_ という方法が[Contribution to Mental Poker](http://www.tdx.cat/bitstream/handle/10803/5804/jcr1de1.pdf)という本のChapter 6で紹介されています。これについて読んで分かったことをまとめます。
また、これをもとにPythonと[Charm-Crypt](http://www.charm-crypto.com/Main.html)を用いて書いたコードが下記のGistにあります。
https://gist.github.com/yoshimuraYuu/d8897e9dce479b620606

# やりたいこと

- TTP（ _Trusted Third Party_ ）を必要としない
- プレイヤーの戦略の秘密性がある

# プロトコル
_Protocol_ や _Procedure_ の数字はもとになったContribution to Mental Pokerに併せているので、妙な番号から始まりますが気にする必要はありません。

## 準備

まず、次の内容は全てのプレイヤーの間の中で共通のものを用います。

- プレイヤーは$P_1$から$P_n$までの$n$人
- $p = 2q + 1 \wedge q > 2$となるような素数$p, q$
- [原始元](http://akademeia.info/index.php?%B8%B6%BB%CF%B8%B5)$\alpha$（この$\alpha$は$p$と[平方非剰余](http://ja.wikipedia.org/wiki/%E5%B9%B3%E6%96%B9%E5%89%B0%E4%BD%99)）
- パラメーター$s$
- 使用するカードは$52$枚
- $X = x_1, \dots, x_i, \dots, x_{52}$（ただし$2 < x_i < q$かつ$x_i$は奇数）

そして、プレイヤー$P_i$は次のような計算をします。

1. $2 < K_i < q$となる任意の奇数をプレイヤー$P_i$の秘密鍵$K_i$とする
2. $\beta_i = \alpha^{K_i}$となる$\beta_i$を他のプレイヤーに公開する
3. $\beta = \alpha^{K_1, \dots, K_n}$となる$\beta$を、$K_i$を公開することなく共有する（この共有には[Diffie-Hellman鍵交換](http://crypto.stackexchange.com/questions/1025/can-one-generalize-the-diffie-hellman-key-exchange-to-three-or-more-parties)を使います）

## カードのシャッフル

直感的なイメージは全てのプレイヤーが裏にした山札を順にシャッフルしてゆくような感じです。

### シャッフルの準備

まず、ここで次のような初期の山札$C_0$をセットします。

```math
C_0 = c_{0, 1}, \dots, c_{0, 52} \\
where\, c_{0,j} = (d_{0,j}, \alpha_{0,j}) = (\alpha^{x_j}, \beta)
```

ここで、いかなる$\alpha^{x_j}$も平方非剰余です。

その後、プレイヤー$P_i$は山札$C_{i-1}$を得て山札$C_i$を生成します。シャッフルを$P_1$から$P_n$まで順番に実行して、最後に$P_n$が生成した山札$C_n$が最終的な山札となります。

### シャッフルの手順（Protocol 47）

1. プレイヤー$P_i$は、一つ前のプレイヤー$P_{i-1}$が計算した山札$C_{i-1}$から _Procedure 32_ を用いて$C_i, R_i, \pi_i$を計算する
2. _Protocol 48_ を用いて、一つ前のプレイヤー$P_{i-1}$が計算した$C_{i-1}$が妥当か検査
3. $C_i$を全てのプレイヤーへ公開する

### 山札の並びの入手（Procedure 32）

まずプレイヤー$P_i$は前のプレイヤー$P_{i-1}$が生成した山札$C_{i-1} = c_1, \dots, c_{52}$（ただし$c_j = (d_j, \alpha_j)$）を用いて次のようにシャッフルを行います。

#### 受け取る情報

- 山札$C$

#### 手順

1. $R = r_1, \dots, r_{52}$という$R$を生成する（ただし$r_j = 2 < r_j < q$を満すランダムな奇数）
2. $c_j' = (d_j^{r_j}, \alpha_j^{r_j})$を$j = 1 \dots 52$について計算する（ただし$j$は$C$の$j$番目）
3. $1, 2, \dots, 52$をランダムに並べた順序$\pi$を生成する
4. $C^* = c_{\pi(1)}', \dots, c_{\pi(52)}'$という$C^*$を得る
5. $C^*, R, \pi$を返す

### 山札のシャッフルと検証（Protocol 48）

プレイヤー$P_i$が山札$C_{i-1}$を入手しても、前のプレイヤー$P_{i-1}$がきちんと山札$C_{i-1}$を計算したのか検証して、自身も _Procedure 32_ で山札$C_i$を計算します。
ただし、検証の際に山札の中味が分ってしまうと公平なゲームにならないので、 _Procedure 32_ で生成した情報$R$を用いて確率的に検証を行います。

#### 受け取る情報

- 前のプレイヤー$P_{i-1}$の山札$C_{i-1}$
- 計算しているプレイヤー$P_i$の山札$C_i$
- 情報$R_i$
- 順序$\pi_i$
- パラメーター$s$

#### 手順

1. プレイヤー$P_i$は$C_{i,k}, R_{i,k}, \pi_{i,k} = \mathit{Procedure\, 32}(C_i)$を得て、$C_{i,k}$を他のプレイヤーへ公開する（$k$は$1$から$s$）
2. $P_i$以外のプレイヤーは$s$桁のランダムなビット列$U = u_i, \dots, u_s$を$P_i$へ送る
3. 送られてきた$u_k \in U$について
  - $u_k = 1$ならば
      1. プレイヤー$P_i$は$R_{i,k}, \pi_{i,k}$を公開する
      2. 他のプレイヤーは _Procedure 33_ で$C_i, C_{i,k}$を検証する
  - $u_k = 0$ならば
      1. プレイヤー$P_i$は$\pi_{i,k}' = \pi_{i,k} \circ \pi_i$と$R_{i,k}' = r_{i,k,1}', \dots, r_{i,k,52}'$を得る（ただし、$r_{i,k,j} = r_{i, \pi_{i,k}'^{-1}(j))} \cdot r_{i, k, \pi_{i,k}(j)}$）
      2. プレイヤー$P_i$は$R_{i,k}', \pi_{i,k}'$を公開する
      3. 他のプレイヤーは _Procedure 33_ で$C_{i-1}, C_{i,k}$を検証する

### 山札の検証（Procedure 33）

#### 受け取る情報

- 山札$C_a$
- 山札$C_b$
- 情報$R$
- 順序$\pi$

#### 手順

山札$C_a$と山札$C_b$について、情報$R$と順序$\pi$がきちんと対応しているのかを山札を先頭から最後まで一枚ずつ検査します。$j$を山札から$j$番目のカードとします。（つまり$1 \le j \le 52$）

1. $c_{b,j} = (d_{d,j}, \alpha_{b,j}) \in C_b$とし、また$c_{a,\pi(j)} = (d_{a,\pi(j)}, \alpha_{a, \pi(j)}) \in C_a$とする
2. $d_{b,j} = (d_{a,\pi(j)})^{r_{\pi(j)}}$かどうか検査する
3. $\alpha_{b,j} = (\alpha_{a, \pi(j)})^{r_{\pi(j)}}$かどうか検査する

## カードのドロー（Protocol 49）

不正の無さを[ゼロ知識証明](http://ja.wikipedia.org/wiki/%E3%82%BC%E3%83%AD%E7%9F%A5%E8%AD%98%E8%A8%BC%E6%98%8E)で示します。

1. プレイヤー$P_u$は、まだ誰もドローしていない山札$C_n$の$j$番目を選び、そのカードを$c_{n,j} = (d_{n,j}, \alpha_{n,j})$とする
2. $P_u$は$e_0 = \alpha_{n,j}$を公開し、$r = 0$とする
3. $i = 1, 2, \dots, u - 1, u + 1, \dots, n$という$i$について、
  1. $r = r + 1$とする
  2. $P_i$は$e_r = (e_{r-1})^{K_i^{-1}}$を公開する
  3. $P_i$はゼロ知識証明で$\log_\alpha{\beta_i} = \log_{e_r}{e_{r-1}}$を証明する。これは[Chaum-Pedersenの証明](http://www.cs.elte.hu/~rfid/chaum_pedersen.pdf)を用いて効果的に行える
4. $P_u$は$e_n = (e_{n-1})^{K_u^{-1}}$を計算する
5. 山札から抜いたカード$x \in X$は$d_{n,j} = (e_n)^x$を満す
6. $P_u$は$x$をカードとして得る

## カードの公開（Protocol 50）

まず、プレイヤー$P_u$は山札の$j$番目のカード$c_{n,j}$をドローするとき、 _Protocol 49_ でプレイヤー$P_n$から$e_{n-1}$を得ていると仮定すると、$e_{n-1}$が _Protocol 49_ の間に得られていて、かつカードが$P_u$のハンドの中にあることが明らかになります。

1. プレイヤー$P_u$は$e_n = (e_{n-1})^{K_u^{-1}}$を公開する
2. ゼロ知識証明で$\log_{e_n}{e_{n-1}} = \log_\alpha{\beta_u}$を証明する。これは[Chaum-Pedersenの証明](http://www.cs.elte.hu/~rfid/chaum_pedersen.pdf)を用いて効果的に行える

全てのプレイヤーは$d_{n,j} = (e_n)^x$を満す$x \in X$を検証できます。

## カードを捨てる

捨てる場合は他のプレイヤー全員にカード$c_{n,j}$を捨てたことを告知します。

# Mental Mahjongへ

いくつかの問題があります。

- ハンドを公開する際に、どのハンドを山札の何番目からドローしたのか公開する必要がある

# 参考

このプロトコルで使われている技術について、さらに細かく調べたものです。

- [安全素数とべき乗と逆元](http://qiita.com/_yyu_/items/6c099ba0480f8fea6513)
- [Chaum-Pedersenの証明](http://qiita.com/_yyu_/items/b2277fceefc5359e591a)
