[A TTP-free mental poker protocol achieving player confidentiality](http://qiita.com/_yyu_/items/8d8c82ba729b06b26e67)では$e_r = (e_{r-1})^{K_i^{-1}}$といった、 _べき根_ のような計算を用いて暗号化や復号化をしている。これを字面通りに行うためには、$e_r = \sqrt[K_i]{e_{r-1}}$という数を求める必要があり、これは（何か効率的な方法があるのかもしれないが）大変になると思われる。
そこで、このプロトコルに利用されるパラメーターの制約とモジュラ数を利用してこのようなべき根を使うことなく計算を行うことを目標とする。
この証明などを考えるにあたって、[@mimizunohimono](https://twitter.com/mimizunohimono)くんに協力していただいた。

# 予備知識

この記事を読むためには次のような知識が必要。

## 安全素数

素数$p, q$が次の式を満すとき、素数$p$を安全素数と言う。

```math
p = 2q + 1
```

## オイラー関数と素数

$\varphi$は[オイラー関数](http://ja.wikipedia.org/wiki/%E3%82%AA%E3%82%A4%E3%83%A9%E3%83%BC%E3%81%AE%CF%86%E9%96%A2%E6%95%B0)であり、$n$を素数とすると次のようになる。

```math
\varphi(n) = n - 1
```

## オイラーの定理

あらゆる$a, n$について次が成り立つ。

```math
a^{\varphi(n)} \equiv 1 \pmod{n}
```

## モジュラ数の逆元

$p$を法とした$e$の逆元$x$は記号$-1$を用いて次のように書く。

```math
e^{-1} \equiv x \pmod{p}
```

ある$e \bmod p$についての逆元$x \equiv e^{-1} \pmod{p}$は次の式を満す。

```math
e e^{-1} \equiv e x \equiv 1 \pmod{p}
```

$p$が素数の時、$\varphi(p) = p - 1$とオイラーの定理から、

```math
e^{p - 1} \equiv 1 \pmod{p}
```

従って、$p$が素数の時$e$の逆元は$e^{p - 2}$となる。
詳しくは[モジュラ逆数（Wikipedia）](http://ja.wikipedia.org/wiki/%E3%83%A2%E3%82%B8%E3%83%A5%E3%83%A9%E9%80%86%E6%95%B0)を見るとよい。

## 平方剰余

互いに素な数$n, p$について

```math
n \equiv x^2 \pmod{p}
```

となる$x$が存在する時、$n$は平方剰余と言い、そうでない時は平方非剰余と言う。

## 合成数のモジュラ計算

$a, b, n$について次が成り立つ。

```math
a b \bmod n = \left((a \bmod n)\; (b \bmod n)\right) \bmod n
```

## 原始根

ある数$g$が$p$の原始根である時、$a < p$となる任意の$a$について次の性質を満たす$x$が存在する。

```math
a \equiv g^x \pmod{p}
```

つまり、$i = 1, 2, \dots, p - 1$について$g^i \bmod p$が全て異なる値になる。

また、適当な素数$p_1, p_2, \dots, p_k$を用いて$\varphi(p) = p_1\times p_2\times \dots\times p_k$の時、次の条件を満すことで$g$が$p$の原始根であると判定できる。

```math
g^{\frac{\varphi(p)}{p_i}} \not\equiv 1 \pmod{p}\; \text{for } i = 1\dots k
```

詳しくは下記のURLにある。
http://en.wikipedia.org/wiki/Primitive_root_modulo_n#Finding_primitive_roots

# プロトコルにあるパラメーターの制約

上記のプロトコルでは次のような制約がある。

- $p, q$は素数であり$p = 2q + 1$かつ$q > 2$
- $K_i$は$q$未満の奇数
- $\alpha$は$p$の原始元であり、$p$と平方非剰余
- $\alpha$にランダムな奇数（$X$や$R$）をべき乗して生成された$e_r$は平方非剰余

# 求めたいこと

$q$を法とした$K_i$の逆元を$K_i^{-1}$として、

```math
(M^{K_i})^{{K_i}^{-1}} \equiv M \pmod{p}
```

ただし、$M$は$p$の原始根であり平方非剰余。

# 証明

まず、$q$を法とした時の$K_i$の逆元を考える。$q$は素数であり、$K_i < q$より$K_i \bmod q = K_i$なので、

```math
K_i^{-1} \equiv K_i^{q - 2} \pmod{q}
```

よって逆元の定義から

```math
K_i K_i^{q - 2} \equiv 1 \pmod{q} \\
K_i^{q - 1} \equiv 1 \pmod{q}
```

この式から、

```math
K_i^{q - 1} = kq + 1
```

を満す$k$が存在する。
また、$K_i$は$q$以下の奇数なので、$n = 0, 1, 2, \dots$を用いて次のように表わせる。

```math
K_i = 2n + 1
```

よって、$(2n + 1)^{q - 1} = kq + 1$の左辺を[二項定理](http://ja.wikipedia.org/wiki/%E4%BA%8C%E9%A0%85%E5%AE%9A%E7%90%86)を用いて展開すると次のようになる。

```math
(2n)^{q-1} + {q-1 \choose 1}(2n)^{q-2} + \dots + {q-1 \choose q-2}(2n) + 1 = kq + 1 \\
(2n)^{q-1} + {q-1 \choose 1}(2n)^{q-2} + \dots + {q-1 \choose q-2}(2n) = kq
```

左辺の項は全て$2n$があるので偶数の足し算となり、左辺全体が偶数となる。$q$は$2$より大きい素数なので奇数であるから、$k$は偶数となる。
よって、$j = 1, 2, 3, \dots$を用いて次のように表わせる。

```math
k = 2j
```

従って、

```math
K_i K_i^{-1} = K_i^{q - 1} = 2jq + 1
```

ゆえに、

```math
(M^{K_i})^{{K_i}^{-1}} \bmod p = M^{K_i K_i^{-1}} \bmod p = M^{2jq + 1} \bmod p
```

となり、

```math
M^{2jq + 1} \bmod p = M M^{2jq} \bmod p = M (M^{2q})^j \bmod p
```

また、$p = 2q + 1$より

```math
2q = p - 1
```

となるので、

```math
M (M^{2q})^j \bmod p = M (M^{p-1})^j \bmod p
```

となり、これを変形すると

```math
M (M^{p-1})^j \bmod p = \left((M \bmod p)\; \left((M^{p-1} \bmod p)^j  \bmod p \right) \right) \bmod p
```

$p$は素数なので、$\varphi(p) = p - 1$からオイラーの定理により、

```math
M^{p-1} \bmod p = 1
```

よって、

```math
\left((M \bmod p)\; 1\right) \bmod p = M \bmod p
```

ゆえに

```math
(M^{K_i})^{{K_i}^{-1}} \bmod p = M \bmod p
```

これにより

```math
(M^{K_i})^{{K_i}^{-1}} \equiv M \pmod{p}
```

となる。

# Mが平方非剰余かつ原始根である理由

$M$が原始根ではないとすると、異なる鍵$K_i, K_j$で暗号化した結果が次のように等しくなる場合がある。

```math
M^{K_i} \equiv M^{K_j} \pmod{p}
```

すると復号化に失敗する可能性があるので、$M$は原始根であり平方非剰余である必要がある。

仮に$M$が原始根であったとしても、$M$を繰り返し暗号化した$M^{K_i} \bmod p$が原始根でなければあまり意味がない。そこで次の二つを述べる。

- 平方非剰余な数は原始根にならない。つまり偶数乗してはならない
- 原始根を特定の奇数（鍵$K_i$の制約）でべき乗した剰余は原始根になる。つまり奇数乗ならばしてもよい

## 平方剰余な数は原始根にならない

$p = 2q + 1$という素数$p, q$について、$M$は平方剰余なので$M \equiv N^2 \pmod{p}$となる$N$が存在する。
この時、

```math
M^q \equiv (N^2)^q \equiv N^{2q} \pmod{p}
```

$2q = p - 1$なので

```math
M^q \equiv N^{p - 1} \equiv 1 \pmod{p}
```

ところが、オイラーの定理から

```math
M^{p - 1} \equiv 1 \pmod{p}
```

つまり

```math
M^q \equiv M^{p - 1} \equiv 1 \pmod{p}
```

$q \ne p - 1$より$M$は原始根ではない。

## 安全素数の原始根を特定の奇数でべき乗した剰余は原始根になる

$p = 2q + 1$となる素数$p, q$、奇数を$2n + 1$（$n = 0, 1, \dots$）、$p$の原始根を$g$とする。原始根を奇数でべき乗した剰余は次のようになる。

```math
g^{2n + 1} \bmod p
```

さらに$\varphi(p) = p - 1 = 2q$なので、次の条件を満せば$g^{2n + 1}$は$p$の原始根となる。

```math
(g^{2n + 1})^2 \not\equiv 1 \pmod{p} \wedge (g^{2n + 1})^q \not\equiv 1 \pmod{p}
```

また

```math
(g^{2n + 1})^2 \equiv g^{2(2n+1)} \pmod{p} \\
(g^{2n + 1})^q \equiv g^{q(2n+1)} \pmod{p}
```
となる。
$g$は原始根であり、かつオイラーの定理から$g^x \equiv 1 \pmod{p}$となる$x$は$p - 1$しかない。よって奇数$2n + 1$は次の条件を満せば$M^{2n + 1} \bmod p$が原始根となる。

```math
2(2n + 1) \ne p - 1 \wedge q(2n + 1) \ne p - 1
```

$p - 1 = 2q$なので、

```math
2n + 1 \ne q \wedge 2n + 1 \ne 2
```

$2n + 1 = 2$となる整数$n$は存在しないので、つまり安全素数$p = 2q + 1$についての原始根$g$を奇数でべき乗した剰余は、奇数が$q$ではない場合に限り$p$の原始根になる。
