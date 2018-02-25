# はじめに

[Scalaで一番よく使うローンパターン](http://qiita.com/piyo7/items/c9be1f39bcfea43a778a)では、ローンパターンの典型的なコードとして次があげられている。

```scala
import java.io.Writer

import scala.io.Source

object Using {
  def apply[A, B](resource: A)(process: A => B)(implicit closer: Closer[A]): B =
    try {
      process(resource)
    } finally {
      closer.close(resource)
    }
}

case class Closer[-A](close: A => Unit)

object Closer {
  implicit val sourceCloser: Closer[Source] = Closer(_.close())
  implicit val writerCloser: Closer[Writer] = Closer(_.close())
}
```

このコードは、リソース（`resource`）を使った関数`process`を受け取ってそれを実行する。もし`process`が成功したとしても、あるいは失敗して例外を送出したとしても、リソースを閉じるために`closer.close(resource)`を呼び出すようになっている。ただ、このコードは著者が主張するようにモナドではないため、`for`式の中で使うことができない。よって、たとえば次のようにいくつものリソースを取り扱う場合はネストする。

```scala
Using(new FileInputStream(getClass.getResource("/source.txt").getPath)) { in =>
  Using(new InputStreamReader(in, "UTF-8")) { reader =>
    Using(new BufferedReader(reader)) { buff =>
      Using(new FileOutputStream("dest.txt")) { out =>
        Using(new OutputStreamWriter(out, "UTF-8")) { writer =>
          var line = buff.readLine()
          while (line != null) {
            writer.write(line + "\n")
            line = buff.readLine()
          }
        }
      }
    }
  }
}
```

また、[Loanパターンを~~モナド~~for式で使えるようにしてみたよ](http://d.hatena.ne.jp/gakuzo/20110630/1309442452)では次のようにして`for`式の中で使えるようにしている。

```scala
class Loan[T <: {def close()}] private (value: T) {

  def foreach[U](f: T => U): U = try {
    f(value)
  } finally {
    value.close()
  }  

}
object Loan {
  
  def apply[T <: {def close()}](value: T) = new Loan(value)
  
}
```

これを用いると先ほどのネストした例を次のように書ける。

```scala
for {
  in     <- Loan(new FileInputStream("source.txt"))
  reader <- Loan(new InputStreamReader(in, "UTF-8"))
  buff   <- Loan(new BufferedReader(reader))
  out    <- Loan(new FileOutputStream("dest.txt"))
  writer <- Loan(new OutputStreamWriter(out, "UTF-8"))
} {
  var line = buff.readLine()
  while (line != null) {
    writer.write(line)
    line = buff.readLine()
  }
}
```

ただ、この例では著者が主張するようにモナドにはなっていない。本記事ではこのようなIOのリソースを適切にクローズするような`Close`モナド[^close_monad]の作成を行う。また作成したモナドに対して[scalaprops](https://github.com/scalaprops/scalaprops)でテストを作成する。なお、全体のソースコードは次のリポジトリにある。

- https://github.com/y-yu/close

[^close_monad]: `Close`モナドは一般的な名前ではなく、筆者が勝手につけた名前である。

# 追記

@jwhaco さんが継続モナドを利用してよりよい実装を公開されていましたので、紹介させていただきます。

- [Loan パターンのネストは継続モナドでシュッと解決できるよという話](http://qiita.com/jwhaco/items/224113324fd454b8ca77)

# `Close`モナド

このモナドの作成はリーダーモナドと[FujiTask](http://qiita.com/pab_tech/items/86e4c31d052c678f6fa6)を参考にした。

```scala:Close.scala
abstract class Close[+R, +A](res: R) { self =>
  protected def process()(implicit closer: Closer[R]): A

  def run()(implicit closer: Closer[R]): A =
    try {
      process()
    } finally {
      closer.close(res)
    }

  def flatMap[AR >: R, B](f: A => Close[AR, B]): Close[AR, B] = new Close[AR, B](res) {
    def process()(implicit closer: Closer[AR]): B =
      try {
        f(self.process()).process()
      } finally {
        closer.close(res)
      }

    override def run()(implicit closer: Closer[AR]): B =
      process()
  }

  def map[B](f: A => B): Close[R, B] = flatMap(x => Close(res, f(x)))
}

object Close {
  def apply[R, A](res: R, a: => A) = new Close[R, A](res) {
    def process()(implicit closer: Closer[R]): A = a
  }

  def apply[R](res: R): Close[R, R] = apply(res, res)
}
```

```scala:Closer.scala
trait Closer[-A] {
  def close(a: A): Unit
}

object Closer {
  def apply[A](f: A => Unit): Closer[A] = new Closer[A] {
    def close(a: A): Unit = f(a)
  }
}
```

まず`Close`モナドは2つの型パラメータを受け取る。型パラメータ`R`はリソースの型を表し、型パラメータ`A`は結果の型を表すようになっている。
また、`flatMap`の内部では新しい`Close`モナドを作成している。`process`メソッドを積んでいく構造になっており、まず自分（`self`）の`process`メソッドを実行し、その結果を`f`に投入してさらに`process`メソッドを呼ぶようになっている。この一連の実行は`try`の中に入れることで、成功したとしても失敗して例外が送出されたとしても`finally`で`closer.close()`が実行されリソースがクローズされるようにしている。
`closer`はリソースの型`R`に対応するリソースをクローズする方法を提供する型クラスのインスタンスである。型クラス`Closer[A]`はリソース`A`をクローズするためのメソッド`close`を持つ。

また、[がくぞさんから指摘](http://qiita.com/yyu/items/b83f079381e47c65ce0e#comment-8ea19c3ce53298446b42)を参考に次の2つの変更を与えた。

1. ~~`res: R`を`res: => R`にしてリソースの掴みっぱなしを無くした~~
  - [kawachiさんの指摘](http://qiita.com/yyu/items/b83f079381e47c65ce0e#comment-ed403e8312826729f657)を受けて`res: R`へ戻した
2. `run`メソッドは最初だけリソースを解放するようにセットしておき、一度でも`map`/`flatMap`が発生すると`process`を呼び出すだけになるようにした。こうすることで指摘にあった未合成の`Close`モナドの`run`でリソースリークする問題に対応した

# `Close`モナドの実行例

さきほどの例を`Close`モナドで書くと次のようになる。

```scala:Main.scala
implicit def closer[R <: Closeable]: Closer[R] = Closer { x =>
  println(s"close: ${x.toString}")
  x.close()
}

(for {
  in     <- Close(new FileInputStream(getClass.getResource("/source.txt").getPath))
  reader <- Close(new InputStreamReader(in, "UTF-8"))
  buff   <- Close(new BufferedReader(reader))
  out    <- Close(new FileOutputStream("dest.txt"))
  writer <- Close(new OutputStreamWriter(out, "UTF-8"))
} yield {
  println("[begin]")

  var line = buff.readLine()
  while (line != null) {
    println(line)
    writer.write(line + "\n")
    line = buff.readLine()
  }

  println("[end]")
}).run()
```

実行すると次のような結果が得られる[^source]。

```
[begin]
This
is
a
pen
[end]
close: java.io.OutputStreamWriter@46cd1743
close: java.io.FileOutputStream@513460bd
close: java.io.BufferedReader@35f61ec8
close: java.io.InputStreamReader@56d5bf00
close: java.io.FileInputStream@788ccd96
```

[^source]: `source.txt`の内容により出力が異なる。

# scalapropsによるテスト

やや複雑になったのでGitHubにあるコードのリンクを貼ることにする。

- [CloseTest.scala](https://github.com/y-yu/close/blob/master/src/test/scala/close/CloseTest.scala)
- [CloseTestHelper.scala](https://github.com/y-yu/close/blob/master/src/test/scala/close/CloseTestHelper.scala)
- [CloseLaws.scala](https://github.com/y-yu/close/blob/master/src/test/scala/close/CloseLaws.scala)

まず`Close[R, A]`の`R`を何か適当に固定して[scalaz](https://github.com/scalaz/scalaz)のモナドインスタンスを作成する。そして後はひたすら`Gen`と`Equal`のインスタンスを作ればよい。ただ、`Gen[Close[R, A]]`の定義において、特定の割合で`run`メソッドが例外を送出するような工夫を行った。
また、モナドの性質とは別に次のようなテストも追加した。

- 合成する前のリソースを`run`した場合にきちんとクローズされるか
- `res1`、`res2`の順で合成した場合に`res2`、`res1`の順でクローズされるか

# まとめ

この記事ではIOのリソースをクローズする`Close`モナドを実装した。よい悪いの議論は別として、`Close`モナドに限らず世の中にあるローンパターンはモナドで書き換え可能であるのではないかと考えている。`Close`モナド以外にも、何かモナドで書き換えると便利になるような例があるかもしれない。
