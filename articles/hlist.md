色々な型の値をまとめて扱う際には**タプル**を用いるが、Scalaのタプルは22個までしか値を入れることができない。もし23個の値を持つタプルが必要な場合は自力でそういうデータ型を作るしかない。しかし、例えば23個のタプルを作ったとしても、次に24個のタプルが欲しくなったらまた作る必要があり、これは大変なことになる。そこで、今回はこの問題を解決するために**Heterogeneous List**（**HList**）を実装することにする。
タプルの話題をしているのに、何故リストが出てくるのかと疑問に思うかもしれない。一般にリストとはある型の要素がいくつか入っているデータ構造であるが、HListは色々な型の要素を投入することができ、かつ値がいくつ入っているのかを管理しているデータ構造である。このようなHListはもはやタプルと同じように扱うことができる。

# アイディア

まず普通のリストについて考える。普通のリストは次のようなデータ型である。

```scala
sealed trait List[A]
case class Cons[A](h: A, t: List[A]) extends List[A]
case object Nil extends List[Nothing]
```

これに対して、HListは次のようになる。

```scala
sealed trait HList
case class HCons[+A, +B <: HList](h: A, t: B) extends HList
sealed trait HNil extends HList
```

注目して欲しいのは、`HCons`の`t`が`HList`ではない点である。ではここに何が入るのかと言うと、例えば`HNil`や`HCons[Int, HNil]`、他にも`HCons[Int, HCons[String, HNil]]`といった、型のリストを入れることができる。この仕組みを用いて、色々な型の値を入れられるが型安全であるという目標を実現する。

# `HList`の定義

まず、HListをデータ型で次のように定義する。

```scala
package hlist

sealed trait HList
case class :*:[+A, +B <: HList](h: A, t: B) extends HList {
  def :*:[C](x: C): C :*: A :*: B = hlist.:*:(x, this)
}
sealed trait HNil extends HList {
  def :*:[A](x: A): A :*: HNil = hlist.:*:(x, this)
}
```

先ほどの例ではコンストラクタに`HCons`を用いていたが、例えば`HCons(a, HCons(b, hnil))`[^hnil]と書くのはやや大変なので、コンストラクタを`:*:`という記号にしてしまって、かつそのメソッドにも`:*:`を加えることで、`a :*: b :*: hnil`という記法が利用できるようになる。
まず、コンストラクタ`:*:`が持つ`:*:`メソッドについて説明する。

[^hnil]: 後で説明するが、`hnil`は型`HNil`を持つ値である。

```scala
def :*:[C](x: C): C :*: A :*: B = hlist.:*:(x, this)
```

ここで`this`は`A :*: B`という型である。それに対して新たに型`C`の値`x`を用いてコンストラクタを呼び出すので、生成される型は`C :*: A :*: B`となる。
`HNil`に関しては次のようになる。

```scala
def :*:[A, B <: HList](x: A): A :*: HNil = hlist.:*:(x, this)
```

`this`が`HNil`なので、生成される型は`A :*: HNil`となる。

# `hnil`

空のHListを表す`hnil`を次のよう定義する。

```scala
val hnil = new HNil {}
```

# `head`と`tail`

HListを操作するメソッド`head`と`tail`を定義する。`head`はHListの先頭の要素を得るメソッドであり、`tail`はHListの先頭以外のHListを得るメソッドである。

```scala
def head[A, B <: HList](l: A :*: B): A = l match {
  case h :*: _ => h
}

def tail[A, B <: HList](l: A :*: B): B = l match {
  case _ :*: t => t
}
```

まず`head`は`A :*: B`型のHListを受け取り、先頭の型`A`を返すので、返り値の型は`A`となる。`tail`は`A :*: B`型のHListを受け取り`B`型のリストを返す。
この`head`と`tail`が正しくできているのか確認してみる。

```scala
val l = 1 :*: "string" :*: 1.0 :*: hnil
head(l) + 1
tail(tail(tail(tail(l)))) // compile error!
```

まず、HList`l`に`Int`や`String`など色々な型の値を入れることに成功しているのが分かる。そして`head`で先頭の要素を取り出すこともできる。最後の例が何故コンパイルエラーになるのかと言うと、まず`l`の型は`Int :*: String :*: Double :*: HNil`となっている。この`l`に対して`tail`を3回用いると`HNil`となってしまい、`tail`が求める型`A :*: B`を満すことができない。ゆえに4回目の`tail`はコンパイルエラーとなる。
このように、HListは今どんな型がどれだけ入っているのかを管理しているので、空のHList（`hnil`）に対する`head`や`tail`をコンパイル時に検出することができる。

# `append`

二つのHListを結合するメソッド`append`を実装したいものの、これは先ほど実装した`head`や`tail`のようには型を定義することができない。なのでややトリッキーなことを行う必要がある。
まず、普通のリストに対して用いる`append`メソッドは次のようになる。

```scala
def append[A](l1: List[A], l2: List[A]): List[A] = l1 match {
  case Nil     => l2
  case x :: xs => x :: append(xs, l2)
}
```

これをHListに対して行うには、どのようにすればよいだろうか。

## 実装の方針

例えば二つのHListを`l1: A`と`l2: B`であるとして、`append`の型はどのようになるのだろうか。ここでは`append`の第一引数の型で場合分けして考えてみる。

### 第一引数のHListが型`HNil`の場合

つまり、第一引数のHListが型`HNil`であり、第二引数のHListが型`A`であるならば、この二つを`append`した結果は次のようになる。

```scala
def append[A <: HList](l1: HNil, l2: A): A
```

これは特に説明の必要はないと思う。

### 第一引数のHListが型`A`の場合に成り立つと仮定して、第一引数のHListの型が`X :*: A`の場合を考える

ここでは、数学的帰納法などでありがちな考え方を導入する。第一引数のHListの型が`A`であり、第二引数のHListの型が`B`である時に、`append`の型が`C`となるということを仮定する。

```scala
def append[A <: HList, B <: HList, C <: HList](l1: A, l2: B): C
```

そして、次に一番目のHListに型`X`の値を一つ足したHListである`X :*: A`について、次のような型を付けることができる。

```scala
def append[A <: HList, B <: HList, C <: HList, X](l1: X :*: A, l2: B): X :*: C
```

さて、これをどのようにScalaのコードへエンコードすればよいのだろうか。

## 型クラスとアドホック多相

このような型付けを行う際には、**型クラス**という機能を用いる。[こちらのサイト](http://chopl.in/blog/2012/11/06/introduction-to-typeclass-with-scala.html)では型クラスを用いることで実現できる**アドホック多相**について、次のように書かれている。

> アドホック多相とは何かというと
>
> - 異なる型の間で共通したインターフェースでの異なる振る舞いを
> - 定義済みの型に対して拡張する
>
> ような多相のことです。

つまり今回のケースでは、同じ`append`メソッドであるものの、第一引数の型によって、次の二つのメソッドへ振り分ける必要がある。

- `append1: (A, HNil) => A`
- `append2: (A, B) => C`を前提として、`append3: (X :*: A, B) => X :*: C`

従って、型クラスを用いてアドホック多相を実現することにする。

## 実装

まず、`append`メソッドの型情報を定義する`HAppend`トレイトを作成する。

```scala
trait HAppend[A <: HList, B <: HList, C <: HList] {
  def append(l1: A, l2: B): C
}
```

この`HAppend`トレイトは、二つのHList（それぞれ型が`A`と`B`）を取り、返り値の型が`C`である`append`メソッドの型情報を定義する。
そして、先ほどの二つの`append`をそれぞれ`appendHNil`と`appendHList`という名前で次のように実装する。

```scala
implicit def appendHNil[A <: HList] = new HAppend[HNil, A, A] {
  def append(l1: HNil, l2: A): A = l2
}

implicit def appendHList[A <: HList, B <: HList, C <: HList, X](implicit i: HAppend[A, B, C]) =
  new HAppend[X :*: A, B, X :*: C] {
    def append(l1: X :*: A, l2: B): X :*: C =
      cons(head(l1), i.append(tail(l1), l2))
  }
```

まず、`appendHNil`の実装について考える。第一引数`l2`の型が`HNil`であるので、`appnend`の結果としては`l2`の値をそのまま返せばよく、従って型も`l2`の型と同じく`A`となる。
`appendHList`については、まず`HAppend[A, B, C]`を満すようなインスタンス`i`が存在することを仮定する。

```scala
(implicit i: HAppend[A, B, C])
```

そして、普通のリストの場合と同じように、`append`メソッドを定義する。

```scala
def append(l1: X :*: A, l2: B): X :*: C =
  cons(head(l1), i.append(tail(l1), l2))
```

少々異なる点は再帰的に用いる`append`メソッドがインスタンス`i`のメソッドになっていることだ。これは、現在定義した`append`メソッドが`(X :*: A, B) => X :*: C`という型を持つのに対して、投入したい引数は`tail(l1): A`と`l2: B`である。`l2`は問題ないが、`tail(l1)`は型`A`なので`X :*: A`と異なりエラーとなる。しかし、先ほど作成したインスタンス`i`は、`append: (A, B) => C`というメソッドを持っているので、これを用いて帰納的な関数に対して型を付けられるようにしている。
また、どうして`appendHNil`の定義が必要なのかと疑問に思うかもしれないが、もしここで`appendHNil`がない場合は常に`appendHList`が呼び出され続けて無限に回り続けてしまう。それを防ぐために、`appendHNil`を用意している。
後は二つの`appendHNil`と`appendHList`を振り分ける`append`を実装すればよい。

```scala
def append[A <: HList, B <: HList, C <: HList](l1: A, l2: B)(implicit i: HAppend[A, B, C]) =
  i.append(l1, l2)
```

# `nth`

タプルやリストでは$n$番目の要素へアクセスする手段を提供している。今回のHListではどのようにそれを実装したらよいだろうか。ちなみに普通のリストに対する`nth`は次のように実装できる。

```scala
def nth[A](l: List[A], n: Int) = l match {
  case x :: xs if n == 0 => x
  case x :: xs           => nth(n - 1, xs)
}
```

## 実装の方針と問題点

そこで`append`の時と同様に場合分けして考えることにする。

- $0$番目にアクセスする場合
- $n$番目にアクセスできると仮定して、$n + 1$番目にアクセスする場合

このように二つに区別すればよさそうな気がするが、実はこれには問題がある。先程の例ではHListが`HNil`または`A :*: HList`のどちらかであるという型情報を用いて分岐させていたが、今回分岐の対象として用いる数字（`Int`）は`0`であっても、その他の数であっても両方`Int`型なので、これを使って分岐させることはできない。

## 自然数の実装

そこで$0$とそれ以外の数字を区別するような型を定義する。自然数の型`Nat`は次のようになる。

```scala
sealed trait Nat
sealed trait Zero extends Nat
case class Succ[A <: Nat](n: A) extends Nat
```

自然数の世界には`Zero`と自然数に1を足す`Succ`が存在する。自然数を操作するためメソッドを次のように定義する。

```scala
object Nat {
  val nzero = new Zero {}
  def succ[A <: Nat](n: A): Succ[A] = Succ(n)
  def pred[A <: Nat](n: Succ[A]): A = n match {
    case Succ(n) => n
  }
}
```

例えば$3$は`succ(succ(succ(nzero)))`と表現でき、その型は`Succ[Succ[Succ[Zero]]]`となる。こうすることで自然数を型の情報へエンコードすることができる。

## 実装

まずは`append`の時と同様に、型クラスに用いるトレイトを定義する。

```scala
trait HNth[A <: HList, B <: Nat, C] {
  def nth(l: A, n: B): C
}
```

そして、次のように二つのメソッドを定義して分岐させる。

```scala
implicit def nthZero[A, B <: HList] = new HNth[A :*: B, Zero, A] {
  def nth(l: A :*: B, n: Zero): A = head(l)
}

implicit def nthN[A <: HList, B <: Nat, C, D](implicit i: HNth[A, B, C]) = new HNth[D :*: A, Succ[B], C] {
  def nth(l: D :*: A, n: Succ[B]): C = i.nth(tail(l), Nat.pred(n))
}

def nth[A <: HList, B <: Nat, C](l: A, n: B)(implicit i: HNth[A, B, C]) =
  i.nth(l, n)
```

このようにすることで、`Zero`の場合と`Succ[Nat]`の場合に上手く分岐させることができる。

# 実装

今回作成したコードは[Gist](https://gist.github.com/y-yu/2bfd682ffb216f7fe1f4)にアップロードしてある。

# まとめ

今回作成したHListを用いれば、100個や200個の型が異なるデータを持つ型安全なリストを扱うプログラムを記述できる。また、型クラスを利用して実用的なプログラムの例を考えることができた。
なお、今回実装したHListは[shapeless](https://github.com/milessabin/shapeless)というライブラリの中に（おそらく）より高機能なものがあるので、実用したい方はそちらを使う方がいいかもしれない。

# 参考文献

- [Strongly Typed Heterogeneous Collections](http://okmij.org/ftp/Haskell/HList-ext.pdf)
- [Scalaで型クラス入門](http://chopl.in/blog/2012/11/06/introduction-to-typeclass-with-scala.html)
