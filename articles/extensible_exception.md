# 続編を書きました

[The Missing Method of Extensible Exception: implicit “transitive”](http://qiita.com/yyu/items/2f1a3b0fdea6251d7f64)

# はじめに

> 注意：
> 記事の中にあるコードは読みやすさのために`import`などを省略しているので、このままでは動かない。動かしたい方は[Githubのリポジトリ](https://github.com/y-yu/ExtensibleException)を使うとよい。

Scalaで例外を取り扱う際には、一般的にデータ型を使って次のように例外の階層構造を設計する。

```scala
trait RootException extends Throwable

case class DatabaseException(m: String) extends RootException

case class HttpException(m: String) extends RootException

trait FileException extends RootException

case class ReadException(m: String) extends FileException

case class WriteException(m: String) extends FileException
```

これは次のような階層構造になっている。

```
RootException
|
+---- DatabaseException
|
+---- HttpException
|
+---- FileException
      |
      +---- ReadException
      |
      +---- WriteException
```

このような状態で、`DatabaseException`と`HttpException`が両方発生するかもしれない処理を`Either`を使って次のように実行したいとする。

```scala
val result = for {
  x <- databaseService(???) // Either[DatabaseException, A]
  y <- httpService(???)     // Either[HttpException, A]
} yield ()
```

`databaseService`は`Either[DatabaseException, A]`を返す関数であり、一方`httpService`は`Either[HttpException, A]`という型を持つ値を返す関数である。しかし、これらの型を`for`式で合成した結果の`result`はどういう型になるだろうか。
`Either`は[共変](http://qiita.com/mtoyoshi/items/bd0ad545935225419327)なので、階層のより上位にある型へとキャストしていくから、この場合`result`の型は`Either[RootException, Unit]`となる。しかし、`RootExcepiton`になってしまっては、もはや`FileExcepion`と区別することができない。
そこで、新たに次のような例外を表わすケースクラスを作成する。

```scala
case class DatabaseAndHttpException(m: String) extends RootException
```

さて、ではこの`DatabaseAndHttpException`を例外の階層に追加しなければならない。そうなると既存にあった`DatabaseException`と`HttpException`を変更しなければならず、[Expression Problem](http://maoe.hatenadiary.jp/entry/20101214/1292337923)が発生してしまう。Expression Problemを回避して、つまりは既存のデータ型に変更を加えることなく、`DatabaseAndHttpException`を挿入することはできないだろうか。

# サブタイピングと型の多様性

次のように、例外の階層構造を`extends`を用いて作成するが、これは型の**サブタイピング**を行っている[^subtyping_vs_inheritance]。

[^subtyping_vs_inheritance]: サブタイピングと継承の違いについては割愛するが、一般的に必ずしも一致しないので、ここではサブタイピングという型の関係にのみ注目する。

```scala
trait RootException extends Throwable

case class DatabaseException(m: String) extends RootException
```

```
RootException
|
+---- DatabaseException
```

このよう場合、`DatabaseException`は`RootException`のサブタイプであると言い、`RootException`は`DatabaseException`のSupertypeであると言う。
そもそも、このような例外（型）の階層構造（サブタイプ関係）をどうして作るのかというと、それはサブタイピングに基づく**多様性**を表現したいからである。サブタイピングの多様性は[プログラム言語論の資料](http://logic.cs.tsukuba.ac.jp/~kam/lecture/plm2011/8-web.pdf)にて次のように説明されている。

> 型Aが型Bのsubtype（部分型）のとき、型Bの式を書くべきところに、型Aの式を書いても良い。

これを今回の例にあてはめると、`DatabaseException`は`RootException`のサブタイプであるので、`RootException`の式を書くべきところに、`DatabaseException`を書いてもよいということになる。また、`HttpException`も`RootException`のサブタイプであるので、`RootException`の式を書くべきところに、`HttpException`の式を書いてもよいということになる。
`Either[DatabaseException, A]`と`Either[HttpException, A]`は左側の型が異なり、通常合成することができないが、サブタイプ関係を使い`DatabaseException`と`HttpException`を共に`RootException`の式とみなすことで、`Either[RootException, A]`として合成が可能になる。
このように、例外の階層構造はサブタイピングという型システムの力を使って行われている。しかし、このままでは最初問題にしたように、階層構造の自由な場所に新たな例外を加えようとすると、型の階層を変更する必要があるのでExpression Problemが発生してしまう。

# 型クラスによる安全なキャスト

通常、型を強引に変更する`asInstanceOf`などを用いた[（ダウン）キャスト](https://ja.wikipedia.org/wiki/%E5%9E%8B%E5%A4%89%E6%8F%9B#.E3.83.80.E3.82.A6.E3.83.B3.E3.82.AD.E3.83.A3.E3.82.B9.E3.83.88)は危険であり、行うべきではない。しかし、安全にある型から別の型へ変換する方法がないかというと、そうでもない。例えば`Int`から`String`へキャストする関数は次のように定義できる。

```scala
def string_of_int(i: Int): String = i.toString
```

このように、ユーザーが定義したキャスト関数ならば、サブタイプ関係がない場合でも安全にキャストを行うことができる。このような**ある型`A`から型`B`へのキャストをユーザーが提供している**という情報を[型クラス](http://halcat0x15a.github.io/slide/functional_scala/#/)として次のように定義する。

```scala:Transform.scala
trait :->[A, B] {
  def cast(a: A): B
}
```

例えば`Int :-> Float`というインスタンス（`impliit`パラメータ）があれば、`Int`から`Float`へ安全にキャストするための関数`cast`が存在するということになる。

```scala
implicit val float_of_int = new :->[Int, Float] {
  def cast(a: Int): Float = a.toFloat
}
```

これを用いて例外の階層構造を拡張可能な形で定義することができる。

# `implicit`パラメータの探索順序

本題に入る前に、Scalaの`implicit`パラメータがどのように探索されるのか知っておく必要がある。
Scalaは次の順序で型クラスのインスタンス（`implicit`パラメータ）を探索する。

1. 現在のスコープ
2. 型クラスに投入された型パラメータのコンパニオンオブジェクト
3. 型クラスに投入された型パラメータのスーパークラスのコンパニオンオブジェクト
4. 型クラスの[コンパニオンオブジェクト](http://www.ne.jp/asahi/hishidama/home/tech/scala/object.html#h_companion_object)

Scalaはまず（1）から順番に`implicit`パラメータを探索し、見つかった時点で探索を打ち切る。

# 例外の拡張

さて、安全なキャスト`A :-> B`を用いて例外の階層を定義するとはどういうことだろうか。先程の例を再び振り替えると、今、`DatabaseException`と`HttpException`の二つを抽象化したような`DatabaseAndHttpException`という例外を作ることで次の`for`式の結果を`Either[DatabaseAndHttpException, Unit]`のようにしたい。

```scala
for {
  x <- databaseService(???) // Either[DatabaseException, A]
  y <- httpService(???)     // Either[HttpException, A]
} yield ()
```

そこでまず、既存の型を変更せず`DatabaseAndHttpException`を定義する。

```scala
case class DatabaseAndHttpException(m: String) extends RootException
```

型のサブタイプ関係は次のようになっている。

```
RootException
|
+---- DatabaseException
|
+---- HttpException
|
+---- FileException
|     |
|     +---- ReadException
|     |
|     +---- WriteException
|
+---- DatabaseAndHttpException
```

そして、`DatabaseException`から`DatabaseAndHttpException`へのキャストと、`HttpException`から`DatabaseAndHttpException`へのキャストをそれぞれ次のように`DatabaseAndHttpException`のコンパニオンオブジェクトに定義する。

```scala:DatabaseAndHttpException.scala
object DatabaseAndHttpException {
  implicit val databaseException = new :->[DatabaseException, DatabaseAndHttpException] {
    def cast(a: DatabaseException): DatabaseAndHttpException =
      DatabaseAndHttpException(s"database: ${a.m}")
  }

  implicit val httpException = new :->[HttpException, DatabaseAndHttpException] {
    def cast(a: HttpException): DatabaseAndHttpException =
      DatabaseAndHttpException(s"http: ${a.m}")
  }
}
```

さて、次は`Either`の`map`と`flatMap`を改造する。これにはScalaの[Pimp my Library Pattern](http://d.hatena.ne.jp/xuwei/20110623/1308787607)を用いる[^as]。

```scala:Implicit.scala
object Implicit {
  implicit class ExceptionEither[L <: RootException, R](val ee: Either[L, R]) {
    def map[L2 <: RootException, R2](f: R => R2)(implicit L2: L :-> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(L2.cast(e))
      case Right(v) => Right(f(v))
    }

    def flatMap[L2 <: RootException, R2](f: R => Either[L2, R2])(implicit L2: L :-> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(L2.cast(e))
      case Right(v) => f(v)
    }

    def as[L2 <: RootException](implicit L2: L :-> L2): Either[L2, R] = ee match {
      case Left(e)  => Left(L2.cast(e))
      case Right(v) => Right(v)
    }
  }
}
```

[^as]: ここで定義されている謎のメソッド`as`については後述する。

このように、`map`と`flatMap`の定義を変更して、`Either[L, R]`を受け取り、`L :-> L2`という`implicit`パラメータを探索して、存在した場合は`implicit`パラメータを用いて`Either[L2, R2]`を返すという関数に変更している。
さっそくこれを試してみよう。

```scala
def left[A](e: A) = Left[A, Unit](e)

val e1 = left(DatabaseException("db error"))
val e2 = left(HttpException("http error"))

val e3 = for {
  a <- e1
  b <- e2
} yield ()
```

しかし、これは次のようなエラーでコンパイルに失敗してしまう。

```
Error:(18, 9) could not find implicit value for parameter L2: utils.:->[utils.DatabaseException,utils.HttpException]
      a <- e1
        ^
```

`DatabaseAndHttpException`は型として`DatabaseException`や`HttpException`と階層関係にないので、Scalaの処理系は`DatabaseAndHttpException`へ`implicit`パラメータの探索を試みない。そこで、先程`map`や`flatMap`と共に定義した`as`メソッドを使って明示的に安全なキャストを行ってやると上手くいく。

```scala
val e3 = for {
  a <- e1
  b <- e2.as[DatabaseAndHttpException]
} yield ()
```

このようにすると、`e2`は`Either[HttpException, Unit]`なので`as`は`HtttException :-> DatabaseAndHttpException`の`implicit`パラメータを探索する。型クラス`:->`の型パラメータに`DatabaseAndHttpException`があるので、`DatabaseAndHttpException`のコンパニオンオブジェクトが探索対象に入り、無事に`implicit`パラメータが見つかる。
このように、`implicit`パラメータによって変換可能な例外同士の有向グラフを作ることで、サブタイプ関係を使わず安全に別の型へ変換して取り扱うことができる。

# 既存の例外階層との互換性

今の時点で、サブタイプ関係による例外の階層はこのようになっている。

```
RootException
|
+---- DatabaseException
|
+---- HttpException
|
+---- FileException
|     |
|     +---- ReadException
|     |
|     +---- WriteException
|
+---- DatabaseAndHttpException
```

この階層を今から`:->`によって全部定義する必要があるとしたら、それは大変である。ここからはサブタイプ関係を用いて構築した例外の階層構造と、今回導入した階層構造の互換性を見ていく。

## 自分自身との互換性

ところで、現状のプログラムはサブタイプ関係を全く無視しているので、例えば次のような`for`式がエラーになってしまう。

```scala
val e4 = for {
  a <- e1
} yield ()
```

```
Error:(20, 9) could not find implicit value for parameter L2: utils.:->[utils.DatabaseException,L2]
      a <- e1
        ^
```

なぜこのようなエラーが発生するかというと、`map`行うためには例え何か適当な型`L`による`Either[L, ?]`から`Either[L, ?]`への`map`であっても`L :-> L`となる`implicit`パラメータが必要であり、それがないのでエラーになってしまう。このような適当な型`L`から`L`へキャストするのは、`L`がどのような型であったとしても次のように書ける[^L_as_A]。

```scala
implicit def self[A]= new :->[A, A] {
  def cast(a: A): A = a
}
```

[^L_as_A]: このメソッド`self`では型パラメータを`L`ではなく`A`としているが、意味的には変わりない。

さて、この`implicit`パラメータを置くのに適した場所はどこかというと、それは`implicit`パラメータの探索順位が低い`:->`のコンパニオンオブジェクトの中だろう。

```scala:Transform.scala
object :-> {
  implicit def self[A] = new :->[A, A] {
    def cast(a: A): A = a
  }
}
```

このようにすることでコンパイルを通すことができる。

## サブタイプ関係による階層との互換性

`FileException`は次のようにサブタイプ関係を利用した階層を持つ例外である。

```scala
trait FileException extends RootException

case class ReadException(m: String) extends FileException

case class WriteException(m: String) extends FileException
```

```
RootException
|
+---- FileException
      |
      +---- ReadException
      |
      +---- WriteException
```

これらを持つ`Either`を`for`で次のようにまとめることはできるだろうか。

```scala
val e5 = left(ReadException("file read error"))
val e6 = left(WriteException("file read error"))

val e7 = for {
  a <- e5
  b <- e6
} yield ()
```

次のようなエラーが発生してしまう。

```
Error:(29, 9) could not find implicit value for parameter L2: utils.:->[utils.ReadException,utils.WriteException]
      a <- e5
        ^
```

これは先ほど、`DatabaseAndHttpException`で出現したエラーと同じなので、`as`メソッドで次のようにすれば解決できそうに思える。

```scala
val e7 = for {
  a <- e5
  b <- e6.as[FileException]
} yield ()
```

しかし、これも次のようなコンパイルエラーとなる。

```
Error:(30, 17) could not find implicit value for parameter L2: utils.:->[utils.WriteException,utils.FileException]
      b <- e6.as[FileException]
                ^
```

どうやら、`WriteException :-> FileException`という`implicit`パラメータを発見できなかったようだ。ただ、このようにサブタイプ関係がある場合はこの`WriteException`や`FileException`に限らず次のような`implicit`パラメータを定義することができる。

```scala
implicit def superclass[A, B >: A] = new :->[A, B] {
  def cast(a: A): B = a
}
```

この定義をよく見ると、型パラメータ`B`が`A`であった時は、先ほど定義した`implicit`パラメータ`self`と同じ振る舞いをするということが明らかである[^a_is_supertype_of_a]。よって`:->`のコンパニオンオブジェクトにはこの`superclass`だけを設置する。

```scala:Transform.scala
object :-> {
  implicit def superclass[A, B >: A] = new :->[A, B] {
    def cast(a: A): B = a
  }
}
```

[^a_is_supertype_of_a]: この時、任意の型`A`は`A >: A`を満す。

このようにすれば、次のコードを実行することができる。

```scala
val e7 = for {
  a <- e5
  b <- e6.as[FileException]
} yield ()
```

# まとめ

安全なキャストを提供する型クラスを用いるように`Either`の`map`や`flatMap`を改造することで、例外の階層構造をアドホックに構築することができるようになる。
この方法は下記の論文を読みつつ考えたものなので、既に誰かがよりよい方法を発表している可能性もある。もし情報をご存知の方はQiitaのコメントなどで連絡して欲しい。

# 参考文献

- [An Extensible Dynamically-Typed Hierarchy of Exceptions](http://community.haskell.org/~simonmar/papers/ext-exceptions.pdf)
