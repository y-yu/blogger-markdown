[Chaum-Pedersenの論文](http://www.cs.elte.hu/~rfid/chaum_pedersen.pdf)に書いてある方法で、[Mental Pokerのカードのドロー](http://qiita.com/_yyu_/items/8d8c82ba729b06b26e67#2-3)に必要な部分をすごく端的に書き下してみました。ただ、僕自身が暗号技術に詳しいわけではなく、間違いを含んでいる可能性があるので、興味を持った方は論文をあたる方がいいでしょう。

Mental Pokerのドローは、暗号化された山札からカードを各プレイヤーの秘密鍵で復号化しながらたらい回しにしていきます。この時に各プレイヤーは本当にそのプレイヤーの持つ秘密鍵で復号化したのかどうかというのは、ゲームの公平性に関わる問題です。例えばあるプレイヤーが偽の鍵で復号しているにも関わらず、それが検出できないならば、誰か一人でも不誠実なプレイヤーがいたらもはやゲームが成り立たなくなります。ただ、プレイヤーの鍵を公開してしまうと山札を全て復号化できてしまうので、つまり他のプレイヤーに自分の手札などの情報が分かってしまい、プレイヤーの戦略が流出してしうので、それはよくないです。
![image.png](https://qiita-image-store.s3.amazonaws.com/0/10815/6892adaa-a209-d2b2-b32e-f51d4e86186a.png)

# 登場人物

<dl>
  <dt>Prover</dt>
  <dd>秘密の鍵を使って計算をしたが、その鍵を<em>Verifier</em>には教えずに本当に自分の鍵を使って計算を行なったということを証明したい人</dd>
  <dt>Verifier</dt>
  <dd><em>Prover</em>が本当に自身の鍵を使って計算を行ったのか検証したい人</dd>
</dl>

# 情報

括弧の中は[上記のプロトコル](http://qiita.com/_yyu_/items/8d8c82ba729b06b26e67#2-3)で対応する変数を表わす。

## Prover, Verifierが両方とも知っている情報

<dl>
  <dt>$g$</dt>
  <dd>特別な性質を持つ乱数（$\alpha$）</dd>
  <dt>$h$</dt>
  <dd><em>Prover</em>の公開鍵$g^x$（$\beta_i$）</dd>
  <dt>$z$</dt>
  <dd><em>Prover</em>の計算の元になる値（$e_{r-1}$）</em></dd>
  <dt>$m$</dd>
  <dd><em>Prover</em>が秘密鍵$x$を用いて計算したとされる値$z^{x^{-1}}$（$e_r$）</dd>
</dl>

## Proverしか知らない情報

<dl>
  <dt>$x$</dt>
  <dd><em>Prover</em>の秘密鍵（$K_i$）</dd>
</dl>

# 何ができるのか

この手法を使うことで、 _Prover_ の公開鍵を作るのに使われた$x$と、 $m$を計算する時に使われた$x$が同じであることを、 _Verifier_ は$x$を知ることなく確かめられます。つまり、 _Verifier_ は

```math
\log_g{h} \stackrel{?}{=} \log_m{z}
```

を検証できますが、$\log_g{h}$や$\log_m{z}$の値（つまり _Prover_ の秘密鍵$x$）を突き止めることはできません。

# プロトコル

1. _Prover_ は乱数$s$を生成して$(a, b) = (g^s, m^s)$を計算し$(a, b)$を _Verifier_ へ送信する
2. _Verifier_ は乱数$c$を生成して _Prover_ へ送信する
3. _Prover_ は$r = s + cx$を計算して _Verifier_ へ送信する
4. _Verifier_ は$g^r \stackrel{?}{=} ah^c$かつ$m^r \stackrel{?}{=} bz^c$を検証する

![protocol.png](https://qiita-image-store.s3.amazonaws.com/0/10815/074b7da3-f7a2-34ce-5401-510ed2dbba60.png)


# どういうことか

検証している式

```math
g^r \stackrel{?}{=} ah^c \wedge m^r \stackrel{?}{=} bz^c
```

は$r = s + cx$なので

```math
g^{s+cx} \stackrel{?}{=} ah^c \wedge m^{s+cx} \stackrel{?}{=} bz^c
```

と同じです。ここで _Verifier_ は$c$を知っていますが、$s$を知らないので _Prover_ の秘密鍵$x$を$r$から求めることはできません。また、$c$は _Verifier_ によって無作為に選ばれるので _Prover_ が都合のいい数を用意することもできません。

また、$a = g^s, b = m^s$なので

```math
g^{s+cx} \stackrel{?}{=} g^s h^c \wedge m^{s+cx} \stackrel{?}{=} m^s z^c
```

さらに$h = g^x$であり、$m = z^{x^{-1}}$より$z = m^x$なので

```math
g^{s+cx} \stackrel{?}{=} g^s {g^x}^c \wedge m^{s+cx} \stackrel{?}{=} m^s {m^x}^c \\
g^{s+cx} \stackrel{?}{=} g^{s+cx} \wedge m^{s+cx} \stackrel{?}{=} m^{s+cx}
```

となるので、 _Prover_ が$h$と$z$、$r$を同じ秘密鍵$x$を用いて計算したならば、この式は真になります。

# 二回のチャレンジ

_Prover_ が$s$を変更しないまま、 _Verifier_ が異なる乱数$c_1, c_2$を送信して、異なる$r_1, r_2$を入手すると _Prover_ の秘密鍵を突き止めることができます。
今、 _Verifier_ が二つの乱数$c_1, c_2$を送信して、次のような$r_1, r_2$を _Prover_ が返したとします。

```math
r_1 = s + c_1 x \\
r_2 = s + c_2 x
```

_Prover_ が正しい$x$を用いていた場合、

```math
g^{r_1} = ah^{c_1} \\
g^{r_2} = ah^{c_2}
```

上の式を下の式で割ると

```math
\frac{g^{r_1}}{g^{r_2}} = \frac{ah^{c_1}}{ah^{c_2}} \\
g^{r_1 - r_2} = h^{c_1 - c_2}
```

よって

```math
h = g^{\frac{r_1 - r_2}{c_1 - c_2}}
```

ゆえに

```math
\log_g{h} = \frac{r_1 - r_2}{c_1 - c_2}
```

$h = g^x$より$\log_g{h} = x$なので$x = \frac{r_1 - r_2}{c_1 - c_2}$となり _Verifier_ に _Prover_ の秘密鍵$x$が計算できてしまいます。
