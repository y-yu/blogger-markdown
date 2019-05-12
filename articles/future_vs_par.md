---
title: 並列処理と参照透過性 — Future vs Par
tags: Scala 関数型プログラミング 非同期処理 並列処理
author: yyu
slide: false
---
# はじめに

Scalaは`Future`を使うことで、他のプログラム言語に比べて気軽に非同期処理・並列処理を記述することができる。ところが、これにはちょっとした問題が潜んでいることを[FP in Scala](http://amzn.asia/fp1Efdz)という本[^fp_in_scala]は教えてくれる。この記事ではScala標準の`Future`にどうした問題があるのだろうかをFP in Scalaの例と比較しつつ説明しながら、最終的には参照透過性との関連について述べたい。

[^fp_in_scala]: この本の邦題は「Scala関数型デザイン&プログラミング ―Scalazコントリビューターによる関数型徹底ガイド」と呼ばれるが、長いので界隈では“FP in Scala”と呼ばれている。

# Scalaの`Future`

まず、Scalaの`Future`を使うことでたとえば数値のリストの合計を得る関数`sum`を次のように書ける。ただ、このコードに登場する型`Future`や`ExecutionContext`はひとまずこの時点では詳細を気にする必要はない。

```scala:SumList.scala
object SumList {
  def sum(ints: IndexedSeq[Int])(implicit ec: ExecutionContext): Future[Int] =
    if (ints.length <= 1)
      Future.successful(ints.headOption.getOrElse(0))
    else
      val (l, r) = ints.splitAt(ints.length  / 2)
      (sum(l) zip sum(r)).map((a, b) => a + b)
}
```

これにどのような問題があるだろうかについて、FP in Scalaでは似たようなデータ構造をはじめから作ることで説明している。

# FP in Scalaの`Par`

ここではFP in Scalaで登場する`Par`というデータ構造を実装する過程で、非同期・並列処理についていろいろと考えていく。

## 並列計算のナイーブ実装とその問題

まず並列処理のデータ構造を自作する。とはいえ、並列処理やスレッドといった部分に対する知識はほとんど必要ない。まず、このデータ構造`Par`をつくる前に、並列処理に対するプリミティブを次のように用意する。

```scala:Par.scala
object Par {
  def unit[A](a: => A): Par[A] = ???

  def get[A](a: Par[A]): A = ???
}
```

この2つのメソッドの実装はひとまず置いておいて、ひとまず機能だけを考えることとする。まずメソッド`unit`は型`A`の**評価される前の式または値**を受け取り、それを別のスレッドで評価するためのデータ構造`Par[A]`を返す。そしてメソッド`get`は並列計算の結果の値を取り出す。これらの具体的なコードは忘れて、これを使うことでたとえばさきほどの関数`sum`を次のように書ける。

```scala:ListSum.scala
object SumList {
  def sum(ints: IndexedSeq[Int]): Int =
    if (ints.length <= 1)
      ints.headOption.getOrElse(0)
    else
      val (l, r) = ints.splitAt(ints.length  / 2)
      val sumL = Par.unit(sum(l))
      val sumR = Par.unit(sum(r))
      Par.get(sumL) + Par.get(sumR)
}
```

このコードは、リストの長さが$0$の場合は`0`を返し、それ以外の場合はリストを半分に分割して左右をそれぞれ別スレッドで再帰的に`sum`へ投入する。その後それぞれの値を`Par.get`で取り出して足し算しその結果を返している。
これで原始的な`Future`もどきができているという気がする。ところが、これはよく考えると**参照透過性**が破壊されるということが分かる。まず、参照透過性の定義について述べる。

<dl>
  <dt>参照透過</dt>
  <dd>式が参照透過であるとは、どのようなプログラムにおいても、プログラムの意味を変えることなく、式をその評価結果に置き換えることができること。</dd>
</dl>

このルールをどの部分が破っているかというと、次の部分である。

```scala
val sumL = Par.unit(sum(l))
val sumR = Par.unit(sum(r))
Par.get(sumL) + Par.get(sumR)
```

参照透過性が保たれているならば、上記の式を次のように置き換えてもプログラムの意味が変化しないはずである。

```scala
Par.get(Par.unit(sum(l))) + Par.get(Par.unit(sum(r)))
```

ところが、この式について考えると足し算の左側である`Par.get(Par.unit(sum(l)))`はその引数である`Par.unit(sum(l))`の計算でブロックしてしまうので、さきほどのように並列実行はされない。従って、`Par.unit`は参照透過ではない部分、つまり副作用があることが明らかである。とはいえ、この副作用は`Par.get`を利用するまでは露呈しないので、計算の最後に`Par.get`を利用したいというのが自然な考えとなる。そのためには`Par.get`を呼び出すことなく`Par[?]`を合成（結合）できると便利そうに思える。

## `map2`により計算の合成

たとえば次のようなメソッド`map2`があれば`Par.get`を利用することなく`sum`を実装できそうである。

```scala:Par.scala
object Par {
  def map2[A, B, C](a: Par[A], b: Par[B])(f: (A, B) => C): Par[C] = ???
}
```

この`map2`の実装はひとまずおいておくとして、これを利用すればさきほどの`sum`は次のようになる。

```scala:SumList.scala
object SumList {
  def sum(ints: IndexedSeq[Int]): Par[Int] =
    if (ints.length <= 1)
      Par.unit(ints.headOption.getOrElse(0))
    else
      val (l, r) = ints.splitAt(ints.length  / 2)
      Par.map2(sum(l), sum(r))((a, b) => a + b)
}
```

このようにしたなら、後は最後に必要になったところで`Par.get`を実行するということができる。よって`sum`はインターフェースを変えることになったものの、参照透過性を得ることに成功した。

## フォークのタイミング

別スレッドで実行するべきときと、そうでもないときがあるだろう。`Par[?]`ではあるもののここでは別スレッドで実行する必要がない、ということを今のAPIでは表現できず、`Par.unit`を使えば常に別スレッドで計算が実行されてしまう。そこで`Par.fork`というメソッドを用意する。これは次のようなインターフェースである。

```scala:Par.scala
object Par {
  def fork[A](a: => Par[A]): Par[A] = ???

  def unit[A](a: A): Par[A] = ???
}
```

`Par.fork`によってもはや`Par.unit`が遅延である必要はなくなる。そして、これがあると次のように`sum`をかきなおすことができる。

```scala:SumList.scala
object SumList {
  def sum(ints: IndexedSeq[Int]): Par[Int] =
    if (ints.length <= 1)
      Par.unit(ints.headOption.getOrElse(0))
    else
      val (l, r) = ints.splitAt(ints.length  / 2)
      Par.map2(Par.fork(sum(l)), Par.fork(sum(r)))((a, b) => a + b)
}
```

こうすることで、どのような場合に別スレッドで実行するのかをプログラマが意図できるようになる。
ところが、`Par.fork`によって他のスレッドで計算を実行するといった場合、スレッドプールなどの情報が必要となる。`Par.fork`の呼び出しとともに適当にスレッドを起動してもよいといえばよいが、通常のプログラムではCPUのコア数などに基づくスレッドプールからスレッドを用意することが多い。ここでは次の2つの選択肢がある。

1. `Par.fork`がスレッドプールの情報を受けとって`Par.fork`の呼び出しと同時にスレッドを分岐させる
2. 計算の結果（型`Par[?]`となる値）を取っておき、`Par.get`がスレッドプールなどの情報を持ち込んで、そのときにスレッドを分岐させる

ここでは`Par.get`のインターフェースを改良して、後者の`Par.get`がスレッドプールなどの情報を受けとってその時にスレッドを分岐させるという選択をすることにする。

```scala:Par.scala
object Par {
  def get[A](ec: ExecutionContext)(a: Par[A]): A
}
```

ここでは冒頭で登場した型`ExecutionContext`を利用している。`ExecutionContext`はScala標準のデータ構造でどのように並列計算を行うかが決められている。

## `Par`の具体的な実装

それではいよいよ`Par.unit`と`Par.get`に具体的な実装を与えよう。コードの全体は次のようになる[^timeout]。

```scala:Par.scala
case class Par[A](f: ExecutionContext => Future[A])

object Par {
  def unit[A](a: A): Par[A] = Par(ec => Future.successful(a))

  def fork[A](a: => Par[A]): Par[A] = Par(ec => a.f(ec))

  def map2[A, B, C](a: Par[A], b: Par[B])(f: (A, B) => C): Par[C] = Par { ec =>
    val fa = a.f(ec)
    val fb = b.f(ec)
    (fa zip fb).map(f)
  }

  def get[A](ec: ExecutionContext)(a: Par[A]): A = Await.result(a.f(ec), Duration.Inf)
}
```

[^timeout]: この例では`get`の実装でタイムアウトとして`Duration.Inf`を利用しているが、これはコードを簡単にするためであり本来きちんとやるならば引数などでタイムアウトを受け取るべきである。

# `Par` vs `Future`

さて、ここまででもしかしたら勘のよい人ならば`Par`と`Future`の違いを分ったかもしれない。違いをまとめると次のようになる。

- `Future`は`Future`を呼び出したときに別スレッドへの分岐が直ちに開始されるが、`Par`は`get`で評価するときにはじめて別スレッドへの分岐が行われる

これにより、Scalaの`Future`は参照透過性を破壊するケースがある。たとえば次のようなコードがあるとする。

```scala
def futureFunctionA(): Future[Int] = ???

def futureFunctionB(): Future[Int] = ???

for {
  a <- futureFunctionA()
  b <- futureFunctionB()
} yield ???
```

これを次のように変数へ代入した形に書き直す。

```scala
def futureFunctionA(): Future[Int] = ???

def futureFunctionB(): Future[Int] = ???

val fa = futureFunctionA()
val fb = futureFunctionB()

for {
  a <- fa
  b <- fb
} yield ???
```

もし参照透過なプログラムであればこの2つはプログラムの意味が等しくなるはずであるが、`Future`は作った瞬間に別スレッドが起動し、また`flatMap`は結果を待ち受けるためブロックする。このことをあわせて考えると、最初の代入しない例では最初の`futureFunctionA`が完了するまで待ち、そして次に`futureFunctionB`を起動するという流れになる。一方で一旦代入するとその時点で`Future`が別スレッドで起動するので、後者の例では2つの`Future`がほぼ同時にスタートしていることとなる。これはプログラムの意味が等しいとは言いがたく、これにより参照透過性が破壊される可能性があるといってよい。
一方で`Par`はこのように書いたとしても`Par.get`を呼び出したときはじめて別スレッドへの分岐をはじめとした計算が実行されるため、このような問題は起きない。

# まとめ

とはいえ、既存の`Future`が完全にダメかというと実用上はほとんど問題がないと感じる。参照透過性が崩れるので、一旦代入するということと代入せずに使うことの間に意味上の区別があるのはちょっと使いにくいだろう。[Monix.Task](https://monix.io/docs/3x/eval/task.html)はこの記事で紹介した`Par`のようにスレッドの起動と合成を分けていると聞いたことがあるので、もし興味がある方はこちらの実装を読んでみたり使ってみることをおすすめする。
またFP in Scalaにはこの他にも興味深い例がいくつも書かれているので、この話題に興味を持たれた方はぜひ購入して読んでみてほしい。

# 参考文献

- [FP in Scala](http://amzn.asia/fp1Efdz)

