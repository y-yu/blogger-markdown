# はじめに

ソーシャルゲームなどに実装された「ガチャ」は、ユーザーがお金を投入すると確率で景品が貰えるという仕組みである。最近は景品のレアさなどに応じた確率を表示する実装が主流となっているが、ガチャの運営が表示した確率と実際の実装が正しいという保証はない。**公平なガチャ**とは、このようなソーシャルゲームのガチャの景品の出現確率を実装に基づいて検証できるようにする研究である。
**量子コンピュータ（量子計算機）**は現在のコンピュータ（古典計算機）とは異なる性質を持つコンピュータである。量子コンピュータが古典計算機と大きく異なることは、計算の状態に虚数や負の数の確率を持つことができる点である。この性質を上手く利用することでたとえば高速な素因数分解といった古典計算機では難しいと考えられている計算を実現している。
この記事では擬似的ではない真の確率を取り扱える量子コンピュータの性質を利用した真に公平なガチャについて解説する。まず、古典計算機で研究されてきた公平なガチャに関して軽く説明しその課題を述べる。次に量子コンピュータに関する解説をし、これを利用した公平なガチャについて述べる。
また、この記事を読み分かりにくいことや質問がある場合には、気軽にコメントなどで教えてほしい。

# 古典計算機における公平なガチャ

今までに研究されてきた公平なガチャには、「コミットメント」という暗号技術を利用する方法と「ブロックチェーン」を利用する方法がある。この節ではこの2つの方法について簡単な説明をし、それぞれの課題を述べる。ただし、古典計算機におけるコミットメントについては簡単におさえておかないと恐らく量子コンピュータで何を改善しようとしているのかが伝わらない可能性があるため、ブロックチェーンによる公平なガチャに比べてやや説明が多めである。

## コミットメントを利用した公平なガチャ

コミットメントとは次のような性質を持つ関数$C$を利用したプロトコルである。

<dl>
  <dt>コミット</dt>
  <dd>送信者はコミットしたい情報$b$と、付加的な情報$r$で作製した暗号文$c := C(b, r)$を受信者へ送信する</dd>
  <dt>公開</dt>
  <dd>送信者はコミットした情報$b$と付加的な情報$r$を受信者に送信し、受信者は$c = C(b, r)$を検証する</dd>
</dl>

そして、この2つの操作には次のようなことが言える。

<dl>
  <dt>隠蔽</dt>
  <dd>コミットのステップでは、受信者はコミットされた値$c$から情報$b$についてなにも分からない</dd>
  <dt>束縛</dt>
  <dd>送信者は受信者へ暗号文$c$を送信した後、コミットした値$b$を変更することができない</dd>
</dl>

このような関数を仮定することで、アリスをガチャの運営、ボブをガチャのユーザーとして次のようにガチャを作ることができる。

1. アリスは乱数$m, r$を生成する
2. アリスはボブに$c := C(m, r)$を送信する
3. ボブはアリスに乱数$n$を送信する
4. アリスはボブに$n \oplus m$と対応する景品を送信し、また$m$と$r$をボブへ公開する[^oplus]
5. ボブは$c = C(m, r)$を検証する

[^oplus]: “$\oplus$”はビットのXORを表す。

ところがコミットメントを利用したガチャには問題がある。
最初の問題は上述した隠蔽・束縛を同時に満す実装は不可能であり、どちらかを無条件に満すならば片方は計算の複雑さに依存させるしかないことである。簡単のため、今は$0$または$1$の1ビットのデータをコミットメントする場合を考える。このときコミットメント$C$の第1引数は1ビットからなるコミットメント$b$であり、第2引数は$n$ビットからなる付加的な情報$r$である。
今、関数$C$が隠蔽・束縛を無条件に満すコミットメント関数であると仮定する。アリスがコミットメント$c := C(b, r)$をボブに送信するとき、$c = C(1 - b, r')$を満すような$r'$が存在しなければならない。そうでなければ、ボブは無限の計算資源を用いて総当たりをするなどして$r$と$b$を特定することができる。ボブが$r$と$b$を特定できるということは、隠蔽の条件を破っているということになる。しかし、もしアリスも無限の計算資源を持っていれば、$c = C(1 - b, r')$を見つけることができるので、$1 - b$をさもコミットメントしたかのように装うことができ、これは束縛の条件を破っているということになる。
このような背理法によって、隠蔽・束縛をどちらも無条件に満すようなコミットメントは実現できない。すると、どちらかが無条件ではなく計算の複雑さに依存していることで厳密な公平性は次のように崩れてしまう。

<dl>
  <dt>隠蔽が計算量に依存している場合</dt>
  <dd>隠蔽が計算の複雑さに依存しているので、ユーザーは計算資源を投入すればコミットメントから元のメッセージを復元することができる。よってユーザーが有利である</dd>
  <dt>束縛が計算量に依存している場合</dt>
  <dd>一方で束縛が計算の複雑さに依存しているので、運営が莫大な計算資源を投入すればコミット後に値を変更できる。よって運営が有利である</dd>
</dl>

このようにコミットメントも完全に公平ではない。より詳細を知りたい方は次のページを見て欲しい。

- [ガチャシステムとコミットメントにおける隠蔽と束縛](https://qiita.com/yyu/items/f172c0cd1e20da09d138)

つまりコミットメントを利用したプロトコルは隠蔽・束縛のどちらかを計算の複雑さに依存させるため、究極的には不公平になってしまう。

## ブロックチェーンを利用した公平なガチャ

ブロックチェーンを利用したガチャの詳細は省くが、直感的なアイディアはブロックチェーンの次のブロックのハッシュ値を予測することが困難である、ということとブロックチェーンを維持するマイナーは不正をしないという仮定のもとに公平であるガチャを構成する。詳細を知りたい方は次のページを見て欲しい。

- [ブロックチェーンを利用した公平なガチャ](https://qiita.com/yyu/items/4eaa43693e39c60a8661)

上記の記事のコメントで @lotz さんが指摘しているように、ブロックチェーンのマイナーは自分の利益を最大にしようとするはずなので、景品の価値がマイニング報酬を上回るような場合にはマイナーが公平かどうかに疑問が生じる。もしマイナーが不正をするならばこのガチャは公平ではなくなる。

# 古典計算機と量子コンピュータ

プロトコルの説明をする前に量子コンピュータの基礎的なことについて言及する。量子コンピュータの説明にはいろいろな方法があると思われるが、この節ではまず古典計算機をベクトルとそれを操作する演算子（行列）で表し、それを拡張して量子コンピュータを構成する。

## 記法

まずは記法について解説する。量子コンピュータの界隈では**ブラケット記法（ディラック記法）**と呼ばれる記法を採用することが多いため、この記事でも同じ記法を用いる。この記法では縦のベクトルを次のように表す。

```math
\def\bra#1{\mathinner{\left\langle{#1}\right|}}
\def\ket#1{\mathinner{\left|{#1}\right\rangle}}
\def\braket#1#2{\mathinner{\left\langle{#1}\middle|#2\right\rangle}}
%
\ket{a} \equiv \left(
  \begin{array}{c}
    \alpha \\
    \beta
  \end{array}
\right)
```

この縦ベクトル$\ket{a}$を横にして複素共役[^conjugate]をとったものを$\bra{a}$とし次のようになる。

$$
\bra{a} \equiv \left(\alpha^{\*}, \beta^{\*}\right)
$$

[^conjugate]: 複素数$\alpha = x + yi$として$\alpha$の複素共役は$\alpha^* = x - yi$となる。

そして、$\ket{b}$を次であるとする。

```math
\ket{b} \equiv \left(
  \begin{array}{c}
    \gamma \\
    \delta
  \end{array}
\right)
```

このとき$\braket{a}{b}$をベクトル$\ket{a}, \ket{b}$の内積であるとして次のように定義する。

```math
\braket{a}{b} = \bra{a}\ket{b} = \left(\alpha^{*}, \beta^{*}\right)\left(
  \begin{array}{c}
    \gamma \\
    \delta
  \end{array}
\right) = \alpha^*\gamma + \beta^*\delta
```

また$n \times n$行列$A$が次のようにあるとする。

```math
A = \left(
  \begin{array}{ccc}
     a_{11} & \dots & a_{1n} \\
     \vdots & \ddots & \vdots \\
     a_{n1} & \dots & a_{nn}
  \end{array}
\right)
```

この記事ではこのような行列$A$を次のように表現する。

```math
A = (a_{ij})_{n \times n}
```

また$\ket{a}\bra{b}$は外積を表す。次のような$\ket{\phi}, \ket{\psi}$があるとする。

```math
\ket{\phi} = \left(\begin{array}{c}
\alpha_1 \\
\vdots \\
\alpha_n \\
\end{array}\right), \;
\ket{\psi} = \left(\begin{array}{c}
\beta_1 \\
\vdots \\
\beta_n \\
\end{array}\right)
```

このとき、これらの外積$\ket{\phi}\bra{\psi}$は次のようになる。

```math
\begin{align*}
\ket{\phi}\bra{\psi} &= (a_{ij})_{n \times n} \\
&\textrm{where} \; a_{ij} = \alpha_i \beta_j^*
\end{align*}
```

## ベクトルによる古典計算機

まず、古典計算機の状態を次の二つのベクトルを用いて表すことにする。

```math
\def\vzero{%
\left(
  \begin{array}{c}
    1 \\
    0
  \end{array}
\right)}
\def\vone{%
\left(
  \begin{array}{c}
    0 \\
    1
  \end{array}
\right)}
\ket{0} \equiv \vzero, \; 
\ket{1} \equiv \vone
```

これらを用いてビットの$0$を$\ket{0}$、ビットの$1$を$\ket{1}$と考える。たとえばビット列“$101$”といった1ビットより大きなビットについては$\ket{0}, \ket{1}$の**テンソル積**を用いて表す。テンソル積を記号$\otimes$で表すとして、ビット列$101$は次のように表す。

```math
\ket{1} \otimes \ket{0} \otimes \ket{1} = \left(
  \begin{array}{c}
    0 \vzero \\
    1 \vzero
  \end{array}
\right) \otimes \ket{1} = \left(
  \begin{array}{c}
    0 \\
    0 \\
    1 \\
    0
  \end{array}
\right) \otimes \ket{1} = \left(
  \begin{array}{c}
    0 \vone \\
    0 \vone \\
    1 \vone \\
    0 \vone
  \end{array}
\right) = \left(
  \begin{array}{c}
     0 \\
     0 \\
     0 \\
     0 \\
     0 \\
     1 \\
     0 \\
     0
  \end{array}
\right)
```

また$\ket{1} \otimes \ket{0} \otimes \ket{1}$といったテンソル積は記号$\otimes$を省略して$\ket{1}\ket{0}\ket{1}$または$\ket{101}$と書くこともある。
さて、このような状態を表現するベクトルに対して演算子を作用させて計算を進めていくことができる。たとえば次のような演算子$X$を考える。

```math
X \equiv \left(
  \begin{array}{cc}
    0 & 1 \\
    1 & 0
  \end{array}
\right)
```

この演算子$X$をたとえば$\ket{0}, \ket{1}$にそれぞれ作用させると次のようになる。

```math
\begin{align}
X\ket{0} = \left(
  \begin{array}{cc}
    0 & 1 \\
    1 & 0
  \end{array}
\right) \vzero = \left(
  \begin{array}{c}
    0 + 0 \\
    1 + 0
  \end{array}
\right) = \vone = \ket{1} \\
X\ket{1} = \left(
  \begin{array}{cc}
    0 & 1 \\
    1 & 0
  \end{array}
\right) \vone = \left(
  \begin{array}{c}
    0 + 1 \\
    0 + 0
  \end{array}
\right) = \vzero = \ket{0} \\
\end{align}
```

つまり、演算子$X$はビットの反転と対応すると言える。このように演算子をベクトルに作用させていくことで、古典計算機で可能な任意の計算を作ることができる。

## ベクトルによる量子コンピュータ

### 量子ビットと確率振幅

量子コンピュータでは、上述したベクトル表現の計算機に複素数で表現される**確率振幅**を利用して拡張したものである。1量子ビット$\ket{\psi}$は次のようになる。

$$
\ket{\psi} \equiv c_0\ket{0} + c_1\ket{1}
$$

ここで複素数$c_0, c_1$は確率振幅と呼ばれ、次を満す必要がある[^abs]。

```math
\def\abs#1{\left|#1\right|}
\abs{c_0}^2 + \abs{c_1}^2 = 1 \label{eq:prob_req}\tag{1}
```

[^abs]: “$|a|$”は$a$の絶対値を表す。

複素数$c_0, c_1$はベクトル$\ket{0}, \ket{1}$のどちらに収束する可能性が高いのかを表す。たとえば次の量子ビット$\ket{+}$を考える。

$$
\ket{+} \equiv \frac{1}{\sqrt{2}}\ket{0} + \frac{1}{\sqrt{2}}\ket{1}
$$

$\abs{\frac{1}{\sqrt{2}}}^2 + \abs{\frac{1}{\sqrt{2}}}^2 = 1$より確率振幅の条件を満す。$\ket{0}, \ket{1}$の確率振幅が等しいので、これは半分の確率（$\abs{\frac{1}{\sqrt{2}}}^2 = \frac{1}{2}$）で$\ket{0}$となり、残りの半分の確率で$\ket{1}$へ収束する量子ビットとなる。

### 測定

では、このように表現された量子ビットが収束した後を表現する方法を考える。この測定もひとつの演算子（行列）として考えることができ、演算子なのでこれは計算のひとつであるといえる。測定は**基底**と呼ばれる内積が$0$となるベクトルの組を用いる。たとえば2つのベクトル$\ket{0}, \ket{1}$の内積$\braket{0}{1}$は次のようになる。

```math
\braket{0}{1} = 1 \times 0 + 0 \times 1 = 0
```

従って$\\{\ket{0}, \ket{1}\\}$は測定に用いることができる。基底として$\\{\ket{0}, \ket{1}\\}$を用いたとすると、測定に用いる演算子$P_0, P_1$は次のようになる。

```math
P_0 \equiv \ket{0}\bra{0} = \left(
  \begin{array}{cc}
    1 & 0 \\
    0 & 0
  \end{array}
\right)
, \; 
P_1 \equiv \ket{1}\bra{1} = \left(
  \begin{array}{cc}
    0 & 0 \\
    0 & 1
  \end{array}
\right)
```

このような演算子$P_0, P_1$をさきほどの演算子$X$のように量子ビットを表すベクトルへ作用させてはならない。なぜなら、古典計算機とは異なり量子コンピュータにおいては演算子を作用させた後であっても確率振幅が式($\ref{eq:prob_req}$)を満す必要がある。このような条件を満す演算子をユニタリ演算子と呼び、演算子$A \equiv (a_{ij})_{n \times n}$がユニタリであるとき次を満す。

```math
\begin{align}
A = A^\dagger &= (b_{ij})_{n \times n} \\
              &\text{where}\; b_{ij} = a^*_{ji}
\end{align}
```

さて演算子$P_0, P_1$をユニタリ演算子とするために、測定前のベクトル$\ket{\psi}$に演算子$P$を作用させたベクトルと$\ket{\psi}$との内積の平方根$\sqrt{\bra{\psi}P\ket{\psi}}$で割る必要がある。最終的に$\ket{\psi} = c_0\ket{0} + c_1\ket{1}$を測定した後のベクトル$\ket{\psi'_0}, \ket{\psi'_1}$は次のようになる。

```math
\ket{\psi'_0} = \frac{P_0}{\sqrt{\bra{\psi}P_0\ket{\psi}}}\ket{\psi}, \; \ket{\psi'_1} = \frac{P_1}{\sqrt{\bra{\psi}P_1\ket{\psi}}}\ket{\psi}
```

たとえば$\ket{+} \equiv \frac{1}{\sqrt{2}}\left(\ket{0} + \ket{1}\right)$があり、$P_0$を利用して測定すると測定後のベクトル$\ket{+'_0}$は次のようになる。

```math
\ket{+'_0} = \frac{P_0}{\sqrt{\bra{+}P_0\ket{+}}}\ket{+} = \sqrt{2}P_0\ket{+} =%
\sqrt{2}\left(
  \begin{array}{cc}
    1 & 0 \\
    0 & 0
  \end{array}
\right)\frac{1}{\sqrt{2}}\left(
  \begin{array}{c}
    1 \\
    1
  \end{array}
\right) = \left(
  \begin{array}{c}
    1 + 0 \\
    0 + 0
  \end{array}
\right) = \left(
  \begin{array}{c}
    1 \\
    0
  \end{array}
\right) = \ket{0}
```

測定が演算子で表されることから分かるように、ある量子ビットを測定した場合、測定後は一般的に状態が変化してしまう。この例では簡単のため$P_0, P_1$の中から$P_0$を選んだが、測定の際にどの演算子が選ばれるかは確率振幅に基づく確率による。たとえば$\ket{+}$は$\ket{0}, \ket{1}$の確率振幅が等しいため、$P_0$と$P_1$のどちらかが等しく$\frac{1}{2}$の確率で選ばれる。
また、さきほどの例では基底$\\{\ket{0}, \ket{1}\\}$を用いた$P_0, P_1$で測定を行ったが、実は他のベクトルを利用して測定することも可能である。たとえば次のようなベクトル$\ket{+}, \ket{-}$を利用して基底$\\{\ket{+}, \ket{-}\\}$で測定することもできる。

```math
\ket{+} \equiv \frac{1}{\sqrt{2}}\left(\ket{0} + \ket{1}\right), \;%
\ket{-} \equiv \frac{1}{\sqrt{2}}\left(\ket{0} - \ket{1}\right)
```

二つのベクトル$\ket{+}, \ket{-}$の内積は次のように$0$である。

```math
\braket{+}{-} = \left(
  \begin{array}{c}
    \frac{1}{\sqrt{2}} \\
    \frac{1}{\sqrt{2}}
  \end{array}
\right) \cdot \left(
  \begin{array}{c}
    \frac{1}{\sqrt{2}} \\
    -\frac{1}{\sqrt{2}}
  \end{array}
\right) = \frac{1}{2} - \frac{1}{2} = 0
```

では$\\{\ket{+}, \ket{-}\\}$を用いて同じように次のような演算子$P_+$を計算する。

```math
P_+ \equiv \ket{+}\bra{+} = \left(
  \begin{array}{c}
    \frac{1}{\sqrt{2}} \\
    \frac{1}{\sqrt{2}}
  \end{array}
\right) \times \left(
  \begin{array}{c}
    \frac{1}{\sqrt{2}} \\
    \frac{1}{\sqrt{2}}
  \end{array}
\right) = \left(
  \begin{array}{cc}
    \frac{1}{2} & \frac{1}{2} \\
    \frac{1}{2} & \frac{1}{2}
  \end{array}
\right) = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 1 \\
    1 & 1
  \end{array}
\right)
```

今、$\ket{+}$の確率振幅に基づく確率により演算子$P_+$が選ばれたとすると、$\ket{+}$の測定後のベクトル$\ket{+'_+}$は次のようになる[^plus]。

```math
\ket{+'_+} = \frac{P_+}{\sqrt{\bra{+}P_+\ket{+}}}\ket{+} = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 1 \\
    1 & 1
  \end{array}
\right)\frac{1}{\sqrt{2}}\left(
  \begin{array}{c}
    1 \\
    1
  \end{array}
\right) = \frac{1}{2\sqrt{2}}\left(
  \begin{array}{c}
    2 \\
    2
  \end{array}
\right) = \frac{1}{\sqrt{2}}\left(
  \begin{array}{c}
    1 \\
    1
  \end{array}
\right) = \ket{+}
```

[^plus]: $\ket{+} = 1\ket{+} + 0\ket{-}$となるため、この場合は必ず$P_+$が選ばれることとなる。

### 混合状態と密度演算子

$1, \dots, n$の$n$個の量子ビット$\ket{\phi_1}, \dots, \ket{\phi_n}$があるとする。この量子ビットが確率$\lambda_i$で発生するとき、それを**混合状態**と呼び、その状態$\rho$を次のように表す。

```math
\rho \equiv \sum_{i = 1}^{n}\lambda_i\ket{\phi_i}\bra{\phi_i}
```

この状態$\rho$のことを**密度演算子**と呼ぶ。たとえば今$\frac{2}{3}$の確率で$\ket{\phi_1}$であり、$\frac{1}{3}$の確率で$\ket{\phi_2}$であるとき、これらの密度演算子は次のようになる。

```math
\frac{2}{3}\ket{\phi_1}\bra{\phi_1} + \frac{1}{3}\ket{\phi_2}\bra{\phi_2}
```

混合状態は、測定する前の量子ビットのような状態がどのビットに収束するかが確定していない状態とは異なり、単に測定する前にどのビットであるか判定することができない状態である。つまり、前者の測定前の量子ビットはまだ状態が確定していないことに対して、後者の混合状態はすでに状態が確定しているものの測定前にはどれかが判断ができないという状態となる。

# 量子コイントス

ここまでの量子コンピュータの知識を利用して、公平なガチャと関連する**量子コイントス**について説明する。量子コイントスとはアリスとボブが量子コンピュータ（と量子通信回線）を用いてコインが裏か表かを公平に予想するためのプロトコルである。コイントスは1ビットの情報であるから、これを$n$回繰り返すことで$2^n$個の景品があるガチャを容易に実装できるため、簡単のためまずは量子コイントスについて説明する。

## BB84プロトコル

初期に提案された量子コイントスのプロトコルである。後に説明するようにこのプロトコルには致命的な脆弱性があるが、最も簡単であるためまずはこのプロトコルを説明する。

1. アリスはランダムに1ビットずつの値$a, x \in \\{0, 1\\}$を作製し、アリスは1量子ビット$\ket{\psi_{a,x}}$を次の中から選び、$\ket{\psi_{a,x}}$をボブへ送信する

    ```math
\begin{align}
\left\{
  \begin{array}{l}
    \ket{\psi_{0,0}} \equiv \ket{0} \\
    \ket{\psi_{0,1}} \equiv \ket{1} \\
    \ket{\psi_{1,0}} \equiv \ket{+} \\
    \ket{\psi_{1,1}} \equiv \ket{-}
  \end{array}
\right.& \\
       &\text{where}\; \ket{\pm} \equiv \frac{1}{\sqrt{2}}\left(\ket{0} \pm \ket{1}\right)
\end{align}
    ```
2. ボブはランダムに$\hat{a} \in \\{0, 1\\}$を作製し、$\mathcal{B}\_{\hat{a}}$を利用して$\ket{\psi_{a,x}}$を測定する。ただし$\mathcal{B}_{\hat{a}}$は次のようになる
    
    ```math
\mathcal{B}_{\hat{a}} \equiv \left\{\ket{\psi_{\hat{a},0}}, \ket{\psi_{\hat{a},1}}\right\}
    ```
3. ボブは(2)で測定した結果を$\hat{x}$とし、ランダムな1ビット$b$をアリスへ送信する
4. アリスは$a, x$を公開する
5. ボブは$a = \hat{a}$ならば$x = \hat{x}$であることを検証する。もしこれが成り立たない場合、プロトコルを中止する
6. $a \oplus b$をコイントスの結果とする

ところが、このプロトコルはいくつかの問題がある。まず、ボブは受け取った$\ket{\psi_{a,x}}$が4つのうちのどれなのかを知ることができるかどうかを考える。このときに密度演算子を利用することができる。もしアリスが$a = 0$であった場合の密度演算子$\rho_0$は次のようになる。

```math
\rho_0 = \frac{1}{2}\ket{0}\bra{0} + \frac{1}{2}\ket{1}\bra{1} = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 0 \\
    0 & 0
  \end{array}
\right) + \frac{1}{2}\left(
  \begin{array}{cc}
    0 & 0 \\
    0 & 1
  \end{array}
\right) = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 0 \\
    0 & 1
  \end{array}
\right)
```

また、アリスが$a = 1$であった場合の密度演算子$\rho_1$は次のようになる。

```math
\rho_1 = \frac{1}{2}\ket{+}\bra{+} + \frac{1}{2}\ket{-}\bra{-} = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 1 \\
    1 & 1
  \end{array}
\right) + \frac{1}{2}\left(
  \begin{array}{cc}
    1 & -1 \\
    -1 & 1
  \end{array}
\right) = \frac{1}{2}\left(
  \begin{array}{cc}
    1 & 0 \\
    0 & 1
  \end{array}
\right)
```

つまり$\rho_0 = \rho_1$である。このように密度演算子が等しい場合、ボブは測定によってアリスの$a$がどちらかを識別することはできない。従ってこのプロトコルはボブが不正をすることはできない。
しかし、アリスは(3)でボブから$b$を受け取った時に$a \oplus b$を計算し、これがアリスにとって望ましくない結果であったならば不正をすることができる。ボブがアリスの不正を検出できるのは(5)で$a = \hat{a}$のときのみであり、そうでなければ無条件でプロトコルは成功となる。今、$a \oplus b = 0$ならばアリスが勝利し、一方で$a \oplus b = 1$ならばボブが勝利するとする。アリスが$a = 0$を選んでいたときに次のような条件分岐となる。

1. ボブが$b = 0$のとき
  - この場合は何もしなくともアリスは勝利するため、アリスはプロトコルを誠実に実行すればよい
2. ボブが$b = 1$のとき
  - この場合、アリスが誠実に振る舞えばボブが勝利してしまう。したがってアリスは不正をしたい。このときのアリスの不正が成功する場合は次のようになる
      1. ボブが$\hat{a} = 0$のとき、アリスが(4)で$a = 1$だと不正をしたとしてもボブは$a \ne \hat{a}$より検証ができないため、アリスは$x$をどのように選んで公開したとしても不正が成功する
      2. ボブが$\hat{a} = 1$のとき、アリスはボブの測定した$\hat{x}$を特定しなければならない。今アリスは$a = 0$を選んだため$\ket{\psi_{0, x}}$は$\ket{0}, \ket{1}$のどちらかである。ボブはアリスから受け取った$\ket{\psi_{0, x}}$を測定する際に、$\hat{a} = 1$より$\\{\ket{+}, \ket{-}\\}$を用いる。このとき測定後のベクトルは次のようになる

          ```math
\begin{align}
\ket{\psi'_{+}} = \frac{P_+}{\sqrt{\bra{\psi_{0, x}}P_+\ket{\psi_{0, x}}}}\ket{\psi_{0, x}} = \ket{+} \\
\ket{\psi'_{-}} = \frac{P_-}{\sqrt{\bra{\psi_{0, x}}P_-\ket{\psi_{0, x}}}}\ket{\psi_{0, x}} = \ket{-}
\end{align}
          ```
          - $\ket{+}, \ket{-}$は共に$\frac{1}{2}$の確率で$\ket{0}$となり$\frac{1}{2}$の確率で$\ket{1}$となる。よってボブの測定結果$\hat{x}$は$\frac{1}{2}$の確率で$0$となり$\frac{1}{2}$の確率で$1$となる。アリスの不正が成功するためには(4)で$x$を送信するときにこのボブの測定結果$\hat{x}$と等しい$x$を当てなければならないが、どちらになるかは完全に等しく$\frac{1}{2}$のランダムである。

これを整理すると、アリスがこの勝負に勝利する確率は次のようになる。

- 普通に勝利する …… $\frac{1}{2}$
- アリスの$a$とボブの$\hat{a}$が一致しない場合、アリスは$a$を偽ってもボブはそれを検証できずに勝利する …… $\frac{1}{4}$
- アリスの$a$とボブの$\hat{a}$が一致する場合、アリスは$x$を$\frac{1}{2}$でボブの測定と一致させたとき勝利する …… $\frac{1}{8}$

つまり、アリスが勝利する確率は$\frac{1}{2} + \frac{1}{4} + \frac{1}{8}$となる。このようなどちらかに有利であるようなプロトコルの有利さを**バイアス**という言葉で表現する。たとえばアリスに対して$\epsilon$バイアスなプロトコルと言った場合、そのプロトコルでアリスが勝利する確率は$\frac{1}{2} + \epsilon$である。いまこのBB84プロトコルはアリスが$\frac{1}{4} + \frac{1}{8} = 0.375$有利なので0.375バイアスなプロトコルである。公平なプロトコルとはアリスもボブもどちらも同じ$\epsilon$バイアスなプロトコルでなければならない。つまりBB84プロトコルは公平なプロトコルではない。
また、さらに致命的な弱点としてBB84プロトコルは“_remote steering_”という攻撃が可能である。この攻撃について説明するためにまずは古典計算機をベクトルで表現する際に用いたテンソル積によるビット表現について考える。量子コンピュータにおいても次のようにあるテンソル積で複数の量子ビットを取り扱うことができる。

```math
\ket{\psi_1} \otimes \ket{\psi_2} \otimes \dots \otimes \ket{\psi_n} = \ket{\psi_1 \psi_2 \dots \psi_n}
```

上記のような$n$量子ビットの表現はたとえある1量子ビットに演算子を作用させたとしても、他の量子ビットに影響を与えない。このような多量子ビット状態を**セパラブル**であると言う。そして量子コンピュータにおいては、ある量子ビットへの演算が他の量子ビットに影響を与えるような多量子ビット状態を考えることができる。たとえば次のようなベル状態と呼ばれる2量子ビットのベクトル$\ket{\psi}$を考える。

```math
\ket{\psi} \equiv \frac{1}{\sqrt{2}}\left(\ket{00} + \ket{11}\right)
```

たとえば、これを次のような演算子$P'_0, P'_1$で測定するとする。

```math
\begin{align}
P'_0 \equiv \ket{0}\bra{0} \otimes I = \left(
  \begin{array}{cccc}
    1 & 0 & 0 & 0 \\
    0 & 1 & 0 & 0 \\
    0 & 0 & 0 & 0 \\
    0 & 0 & 0 & 0
  \end{array}
\right), &\; P'_1 \equiv \ket{1}\bra{1} \otimes I = \left(
  \begin{array}{cccc}
    0 & 0 & 0 & 0 \\
    0 & 0 & 0 & 0 \\
    0 & 0 & 1 & 0 \\
    0 & 0 & 0 & 1
  \end{array}
\right)\\
  &\text{where}\; I = \left(
    \begin{array}{cc}
      1 & 0 \\
      0 & 1
    \end{array}
  \right)
\end{align}
```

このように多量子ビットを測定する際は単位行列$I$とのテンソル積を取る。$\ket{\psi}$の測定後のベクトルをそれぞれ$\ket{\psi'_0}, \ket{\psi'_1}$とすると次のようになる。

```math
\begin{align}
\ket{\psi'_0} = \frac{P'_0}{\sqrt{\bra{\psi}P'_0\ket{\psi}}}\ket{\psi} = \sqrt{2}P'_0\ket{\psi} = \left(
  \begin{array}{c}
    1 \\
    0 \\
    0 \\
    0
  \end{array}
\right) = \ket{00} \\
\ket{\psi'_1} = \frac{P'_1}{\sqrt{\bra{\psi}P'_1\ket{\psi}}}\ket{\psi} = \sqrt{2}P'_1\ket{\psi} = \left(
  \begin{array}{c}
    0 \\
    0 \\
    0 \\
    1
  \end{array}
\right) = \ket{11}
\end{align}
```

つまり、測定のときに演算子$P'_0$が選ばれた場合は2つの量子ビットがどちらも$\ket{0}$となり、逆に$P'_1$が選ばれた場合は2つの量子ビットがどちらも$\ket{1}$となる。このようにいずれかの量子ビットに演算子を作用させると、他の量子ビットにも作用が発生する。なお、このような作用は多量子ビットがどういった距離にあっても発生すると考えられている。従ってアリスはこのような多量子ビットを用いた次のような攻撃が可能である。

1. アリスは2量子ビット$\ket{\psi} \equiv \frac{1}{\sqrt{2}}\left(\ket{00} + \ket{11}\right)$を作製し、片方の量子ビットをボブへ送信する
2. ボブが(2)で測定した後、アリスは$\ket{\psi}$のもう片方の量子ビットを測定することで、アリスはボブの測定結果$\hat{x}$を知ることができる

アリスはボブの測定結果$\hat{x}$を知ることができるため、さきほどの議論によりアリスは自由に不正ができる。従ってこのプロトコルは0.5バイアスとなり完全に壊れる。

## ロス耐性プロトコル

次にBB84プロトコルを改良したプロトコルを紹介する。

1. アリスはランダムに$a, x \in \\{0, 1\\}$を選び、次の量子ビット$\ket{\varphi_{a, x}}$を選択しボブへ送信する

    ```math
\left\{
  \begin{array}{l}
    \ket{\varphi_{0,0}} \equiv \alpha\ket{0} + \beta\ket{1} \\
    \ket{\varphi_{0,1}} \equiv \beta\ket{0} - \alpha\ket{1} \\
    \ket{\varphi_{1,0}} \equiv \alpha\ket{0} - \beta\ket{1} \\
    \ket{\varphi_{1,1}} \equiv \beta\ket{0} + \alpha\ket{1}
  \end{array}
\right.
    ```
    - ただし$1 > \alpha > \beta > 0$かつ$\alpha^2 + \beta^2 = 1$である
2. ボブはランダムに$\hat{a} \in \\{0, 1\\}$を作製し、$\mathcal{B}'\_{\hat{a}}$を利用して$\ket{\varphi_{a,x}}$を測定する。ただし$\mathcal{B}'_{\hat{a}}$は次のようになる
    
    ```math
\mathcal{B}'_{\hat{a}} \equiv \left\{\ket{\varphi_{\hat{a},0}}, \ket{\varphi_{\hat{a},1}}\right\}
    ```
3. ボブは(2)で測定した結果を$\hat{x}$とし、ランダムな1ビット$b$をアリスへ送信する
4. アリスは$a, x$を公開する
5. ボブは$a = \hat{a}$ならば$x = \hat{x}$であることを検証する。もしこれが成り立たない場合、プロトコルを中止する
6. $x \oplus b$をコイントスの結果とする
  - BB84とは異なり$x$と$b$のXORを計算していることに注意せよ

まず、量子ビット$\ket{\varphi_{a, x}}$について考える。これを図とすると次のようになる。

<!--
\def\ket#1{\mathinner{\left|{#1}\right\rangle}}
\begin{tikzpicture}
  \coordinate (O) at (1,2);
  \def\radius{2.5cm}

  \draw (O) circle[radius=\radius];

  \path (O) ++(90:\radius) coordinate (1);
  \path (O) ++(67.5:\radius) coordinate (11);
  \path (O) ++(45:\radius) coordinate (+);
  \path (O) ++(22.5:\radius) coordinate (00);
  \path (O) ++(0:\radius) coordinate (0);
  \path (O) ++(-22.5:\radius) coordinate (10);
  \path (O) ++(-45:\radius) coordinate (-);
  \path (O) ++(-67.5:\radius) coordinate (01);
  \path (O) ++(-90:\radius) coordinate (-1);

  \fill (0) ++(0:1em) node {$\ket{0}$};
  \draw (O)--(0);

  \fill (11) ++(67.5:1em) node {$\ket{\varphi_{1, 1}}$};
  \draw (O)--(11);  

  \fill (+) ++(45:1em) node {$\ket{+}$};
  \draw[dashed] (O)--(+);

  \fill (00) ++(22.5:1.4em) node {$\ket{\varphi_{0, 0}}$};
  \draw (O)--(00);
   
  \fill (1) ++(90:1em) node {$\ket{1}$};
  \draw (O)--(1);

  \fill (10) ++(-22.5:1.4em) node {$\ket{\varphi_{1, 0}}$};
  \draw (O)--(10);

  \fill (-) ++(-45:1em) node {$\ket{-}$};
  \draw[dashed] (O)--(-);

  \fill (01) ++(-67.5:1em) node {$\ket{\varphi_{0, 1}}$};
  \draw (O)--(01);

  \draw (O)--(-1);
\end{tikzpicture}
-->

![image.png](https://qiita-image-store.s3.amazonaws.com/0/10815/d7347647-5e15-5b30-554a-3c96c0600305.png)

この図は$\alpha, \beta$の値については正確ではないが、$\ket{\varphi_{0, 0}}, \ket{\varphi_{0, 1}}$が直交[^orthogonal]していることや$\ket{\varphi_{1, 0}}, \ket{\varphi_{1, 1}}$が直交していることは正確である。
このプロトコルにおけるアリスのバイアスを$\epsilon_A$とし、またボブのバイアスを$\epsilon_B$とする。このとき$\alpha, \beta$を上手く設定することにより$\epsilon_A = \epsilon_B$を達成することができる。

[^orthogonal]: ベクトルが直交しているとは、それらの内積が$0$であることを意味する。

### アリスの不正戦略

まずはアリスがこのプロトコルに対してどのように不正ができるかを考える。今$x \oplus b = 0$ならばアリスの勝利であり、$x \oplus b = 1$ならばボブの勝利とする。まずアリスは(1)で$\ket{\varphi_{a, x}}$ではなく$\ket{+}$を送信する。そしてアリスは(4)の公開のときに$a$として$0 \oplus b$を公開し$x$としても$0 \oplus b$を公開するすると次のようになる。ただし$0$はアリスが勝利する結果のことである。

1. (3)でボブが$b$を公開したとき、$\hat{a} \ne 0 \oplus b$である場合
  - このときアリスの不正をボブは検出することができないため、アリスの不正は常に成功する
  - なぜなら$\hat{a} \ne 0 \oplus b$よりボブはアリスの不正を検出できない
2. (3)でボブが$b$を公開したとき、$\hat{a} = 0 \oplus b$である場合
  - アリスが(4)で公開する値により、ボブはアリスが(1)で$\ket{\varphi_{0 \oplus b, 0 \oplus b}}$を選んだと考える。ところがアリスが(1)で本当に送信した量子ビットは$\ket{+}$である。従って$\ket{+}$を測定した後の結果が$\ket{\varphi_{0 \oplus b, 0 \oplus b}}$へ収束する確率が、アリスの不正が成功する確率となる。この確率は次のようになる

      ```math
\left|\braket{+}{\varphi_{0 \oplus b, 0 \oplus b}}\right|^2 = \left\{
  \begin{array}{l}
    \left|\braket{+}{\alpha\ket{0} + \beta\ket{1}}\right|^2 = \left|\frac{1}{\sqrt{2}}(\alpha + \beta)\right|^2 \\
    \left|\braket{+}{\beta\ket{0} + \alpha\ket{1}}\right|^2 = \left|\frac{1}{\sqrt{2}}(\beta + \alpha)\right|^2
  \end{array}
\right\} = \frac{(\alpha + \beta)^2}{2}
      ```
  - $a^2 + b^2 = 1$より、$\frac{(\alpha + \beta)^2}{2} = \frac{1 + 2\alpha\beta}{2}$である

したがって、アリスの勝率は次のようになる。

```math
\frac{1}{2} + \frac{1}{2}\left(\frac{1 + 2\alpha\beta}{2}\right)
```

バイアスの定義より上記の式から$\frac{1}{2}$を引いて、このプロトコルにおけるアリスのバイアス$\epsilon_A$は次のようになる。

```math
\epsilon_A = \frac{1 + 2\alpha\beta}{4}
```

### ボブの不正戦略

まず、アリスが$x$を$0$または$1$のどちらにしたかによる密度演算子を$\varrho_0, \varrho_1$とすると次のようになる。ただし、BB84とは異なりボブは$x$について情報を得たいため次のようになる。

```math
\begin{align}
\varrho_0 = \frac{1}{2}\ket{\varphi_{0, 0}}\bra{\varphi_{0, 0}} + \frac{1}{2}\ket{\varphi_{1, 0}}\bra{\varphi_{1, 0}} = \left(
  \begin{array}{cc}
    \alpha^2 & 0 \\
    0 & \beta^2
  \end{array}
\right) \\
\varrho_1 = \frac{1}{2}\ket{\varphi_{0, 1}}\bra{\varphi_{0, 1}} + \frac{1}{2}\ket{\varphi_{1, 1}}\bra{\varphi_{1, 1}} = \left(
  \begin{array}{cc}
    \beta^2 & 0 \\
    0 & \alpha^2
  \end{array}
\right) \\
\end{align}
```

このように密度演算子が異なる場合、ボブは測定によって$x$を当てられる確率は次のようになる。ただし$\text{Tr}$は行列の対角成分の和を求める関数である。

```math
\begin{align}
\frac{1}{2} + \frac{1}{4}\text{Tr}\left(\left|\varrho_0 - \varrho_1\right|\right) \label{eq:2}\tag{2}
\end{align}
```

まず、$\varrho_0 - \varrho_1$について考える。$\varrho_0 - \varrho_1$は次のようになる。

```math
\varrho_0 - \varrho_1 = \left(
  \begin{array}{cc}
    \alpha^2 - \beta^2 & 0 \\
    0 & \beta^2 - \alpha^2
  \end{array}
\right)
```

これの絶対値$\left|\varrho_0 - \varrho_1\right|$は$1 > \alpha > \beta > 0$より次のようになる。

```math
\left|\varrho_0 - \varrho_1\right| = \left(
  \begin{array}{cc}
    \alpha^2 - \beta^2 & 0 \\
    0 & \alpha^2 - \beta^2
  \end{array}
\right)
```

従って、式($\ref{eq:2}$)は次のようになる。

```math
\frac{1}{2} + \frac{1}{4}\text{Tr}\left(\left|\varrho_0 - \varrho_1\right|\right) = \frac{1}{2} + \frac{1}{2}\left(\alpha^2 - \beta^2\right)
```

よってボブのバイアス$\epsilon_B$は次のようになる。

```math
\epsilon_B = \frac{1}{2}\left(\alpha^2 - \beta^2\right) = \frac{1}{2}\left(2\alpha^2 - 1\right) = \alpha^2 - \frac{1}{2}
```

### 公平なバイアス

ここまでの議論でアリスとボブのバイアスはそれぞれ次のようになると分った。

```math
\epsilon_A = \frac{1 + 2\alpha\beta}{4}, \; \epsilon_B = \alpha^2 - \frac{1}{2}
```

よって、この2つが等しいという次の方程式を解けばよい。ただし$1 > \alpha > \beta > 0$である。

```math
\left\{
  \begin{array}{l}
    \frac{1 + 2\alpha\beta}{4} = \alpha^2 - \frac{1}{2} \\
    \alpha^2 + \beta^2 = 1
  \end{array}
\right.
```

すると$\alpha, \beta$は次のようになる。

```math
\alpha = \sqrt{0.9}, \; \beta = \sqrt{0.1}
```

そしてアリスとボブのバイアスはともに$\epsilon_A = \epsilon_B = 0.4$となる。このプロトコルは2人のバイアスが等しいため、公平に不正ができるプロトコルという意味で公平であると言える。

# まとめ

量子コンピュータを利用して公平なガチャの最も簡単なものであるコイントスを実装する方法を紹介した。これを公平なガチャへ拡張するのは容易だろうと思われるが、実は具体的なプロトコルを構築してはいないので、もし次があれば具体的な公平な量子ガチャのプロトコルを考案したい。また、このプロトコルは量子コンピュータが実用化したときに実用できるかというと、筆者はそうではないと考えている。なぜならこのプロトコルには量子ビットをそのまま送信できる量子通信回線を必要とするからである。最後に、この記事を読み量子コンピュータや量子コイントスについて興味を持った方は、ぜひ参考文献を読んでみてほしい。

# 謝辞

この記事を書くにあたって、量子コンピュータの説明などに関して様々な助言を頂いた[@kamakiri_ys](https://twitter.com/kamakiri_ys)さんに感謝する。また量子コンイトスについて私に教えてくださった[@iKodack](https://twitter.com/ikodack)さんに感謝する。

# 参考文献

- [Fair Loss-Tolerant Quantum Coin Flipping](https://arxiv.org/abs/0904.3945)
- [量子計算理論](http://amzn.asia/fazovr9)
- [量子コンピュータ手習い](http://c90.yie.jp/)
- [観測に基づく量子計算](http://amzn.asia/5iTasuh)
- [量子プログラミングの基礎](http://amzn.asia/g3GYTXa)
- [量子情報理論とその難しさ —より多くの人に知ってもらうために—](https://www.jstage.jst.go.jp/article/essfr/3/1/3_1_1_44/_pdf)
