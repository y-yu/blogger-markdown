# はじめに

前回の記事、[階層構造を容易に拡張できる例外](http://qiita.com/yyu/items/07d56112bc42938aee05)では`:->`という型クラスを用いて例外（エラー値）[^exception]の階層構造を作るという内容を紹介した。しかし、`A :-> B`と`B :-> C`という二つのインスタンスがあったとしても、`A :-> C`が作られないので不便であった。そこで今回は`A :-> B`と`B :-> C`という二つのインスタンスから`A :-> C`を作るためのインスタンス`transitive`を作成する。
この記事はまず前回の記事で紹介した方法について述べ、その後前回の手法の課題を説明する。そして、今回作成した`transitive`について説明する。
なお、この記事で紹介するコードの完全なものは、次のリポジトリにある。

https://github.com/y-yu/ExtensibleException

この記事を読んで分かりにくい部分や改善案を思いついた場合は、コメントなどで気軽に教えて欲しい。

[^exception]: この記事では、“エラー値”と“例外”という言葉を特に区別せずに使う。

# 階層構造を容易に拡張できる例外の課題

## 階層構造を容易に拡張できる例外

まず、前回の記事の内容を説明する。一般的な継承を用いた例外を次のように作ったとする。

```scala
trait RootException extends Throwable

case class DatabaseException(m: String) extends RootException

case class HttpException(m: String) extends RootException

trait FileException extends RootException

case class ReadException(m: String) extends FileException

case class WriteException(m: String) extends FileException
```

これは次のような階層構造になっている。

```text
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

ここに、データベースの例外とHTTPの例外をまとめた例外`DatabaseAndHttpException`を次のように作るものとする。


```scala
case class DatabaseAndHttpException(m: String) extends RootException
```

すると、継承による階層構造は次のようになる。

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

しかし、このままでは`Either`などで次のように書いた場合に望んだ結果にならない。

```scala
val e1 = for {
  a <- Left(DatabaseException("db errer"))
  b <- Left(HttpException("http errer"))
} yield ???
```

この時、`e`の結果は`DatabaseException`と`HttpException`の共通の親である`RootException`となってしまい、この時、型の上では`FileException`と区別がつかなくなる。
そこで、次のような型クラス`:->`を用いて継承を用いない例外の階層を構築する[^cast]。

```scala
trait :->[-A, +B] {
  def apply(a: A): B
}
```

[^cast]: 前回の記事では`cast`というメソッド名を使っていたが、プログラムが冗長になるので`apply`というメソッド名に変更した。

この型クラスは関数のような、`A`から`B`への安全な変換を定義するものであり、`:->`のインスタンスを次のように作成する。

```scala
object DatabaseAndHttpException {
  implicit val databaseException = new (DatabaseException :-> DatabaseAndHttpException) {
    def apply(a: DatabaseException): DatabaseAndHttpException =
      DatabaseAndHttpException(s"database: ${a.m}")
  }

  implicit val httpException = new (HttpException :-> DatabaseAndHttpException) {
    def apply(a: HttpException): DatabaseAndHttpException =
      DatabaseAndHttpException(s"http: ${a.m}")
  }
}
```

そして、自明なインスタンスを`:->`のコンパニオンオブジェクトに定義しておく。

```scala
implicit def self[A]: A :-> A = new (A :-> A) {
  def apply(a: A): A = a
}

implicit def superclass[A, B >: A]: A :-> B = new (A :-> B) {
  def apply(a: A): B = a
}
```

この型クラスのインスタンスがある場合はユーザーが定義した“安全な変換”ができるので、このインスタンスを使うように`Either`の`map`と`flatMap`を書き換える。

```scala
object Implicit {
  implicit class ExceptionEither[L <: RootException, R](val ee: Either[L, R]) {
    def map[L2 <: RootException, R2](f: R => R2)(implicit L2: L :-> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(L2(e))
      case Right(v) => Right(f(v))
    }

    def flatMap[L2 <: RootException, R2](f: R => Either[L2, R2])(implicit L2: L :-> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(L2(e))
      case Right(v) => f(v)
    }

    def as[L2 <: RootException](implicit L2: L :-> L2): Either[L2, R] = ee match {
      case Left(e)  => Left(L2(e))
      case Right(v) => Right(v)
    }
  }
}
```

このようにすることで、次のように書くことができる。

```scala
val e2 = for {
  a <- Left(DatabaseException("db errer"))
  b <- Left(HttpException("http errer")).as[DatabaseAndHttpException]
} yield ???
```

さきほどとは違い、`e2`の結果が`DatabaseAndHttpException`となり、型の上でも`FileException`など他の例外と区別することができる。

## 課題

この方法では冒頭に述べたように、`A :-> B`と`B :-> C`というインスタンスがあったとしても、`A :-> C`が作られない。これに対しては次のようなインスタンスを定義すればよいと思うかもしれない。

```scala
implicit def transitive[A, B, C](implicit F: A :-> B, G: B :-> C): A :-> C = new (A :-> C) {
  def apply(a: A): C = G(F(a))
}
```

しかし、これでは次のようにimplicitパラメータの探索に失敗してしまう。

```
diverging implicit expansion for type utils.:->[exceptions.HttpException,B]
```

これは、`transitive`のimplicitパラメータ`F`を検索するときに`transitive`が参照され、という無限ループが発生しているものと思われる。

# `transitive`の定義

次のような方法で`transitive`を定義する。

1. 既存の型クラス`:->`の名前を`:~>`へ変更する
2. $A \rightarrow B, B \rightarrow C \Rightarrow A \rightarrow C$のような推移を含まない**ワンステップ**の変換を表す専用の型クラス`:->`を用意する
3. `:->`を用いて`transitive`を定義する

## 型クラス`:->`の名前を`:~>`へ変更

まず、implicitパラメータの発散を防止するために、既存の型クラスの名前を変更し次のようにする[^compose]。

```scala:Transform.scala
trait :~>[-A, +B] { self =>
  def apply(a: A): B
  def compose[C](that: B :~> C): A :~> C = new :~>[A, C] {
    def apply(a: A): C = that(self(a))
  }
}
```

[^compose]: 付け加えて、手動で`transitive`のようなインスタンスを生成するためのメソッド`compose`を用意した。

型クラスの名前を変えたので、`Either`の`map`と`flatMap`も次のように変更が必要である[^throwable]。

```scala:Implicit.scala
object Implicit {
  implicit class ExceptionEither[L1 <: Throwable, R1](val ee: Either[L1, R1]) {
    def map[L2 <: Throwable, R2](f: R1 => R2)(implicit F: L1 :~> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(F(e))
      case Right(v) => Right(f(v))
    }

    def flatMap[L2 <: Throwable, R2](f: R1 => Either[L2, R2])(implicit F: L1 :~> L2): Either[L2, R2] = ee match {
      case Left(e)  => Left(F(e))
      case Right(v) => f(v)
    }

    def as[L2 <: Throwable](implicit F: L1 :~> L2): Either[L2, R1] = ee match {
      case Left(e)  => Left(F(e))
      case Right(v) => Right(v)
    }
  }
}
```

[^throwable]: 前回は`L1`や`L2`の上限として`RootException`を用いていたが、より汎用的にするために今回は`Throwable`を用いている。

そして、自明なインスタンスを定義する。

```scala:Trasform.scala
object :~> {
  implicit def self[A]: A :~> A = new (A :~> A) {
    def apply(a: A): A = a
  }

  implicit def superclass[A, B >: A]: A :~> B = new (A :~> B) {
    def apply(a: A): B = a
  }
}
```

## ワンステップの変換を表わす型クラス`:->`の定義

そして、ワンステップの変換しか含まない型クラス`:->`を定義する。

```scala:Transform.scala
trait :->[-A, +B] {
  def apply(a: A): B
}
```

そして、例外間の関係（ツリー）はワンステップなので、型クラス`:->`のインスタンスとして定義する。

```scala:Exceptions.scala
object DatabaseAndHttpException {
  implicit val databaseException = new (DatabaseException :-> DatabaseAndHttpException) {
      def apply(a: DatabaseException): DatabaseAndHttpException =
        DatabaseAndHttpException(s"database: ${a.m}")
    }

  implicit val httpException = new (HttpException :-> DatabaseAndHttpException) {
      def apply(a: HttpException): DatabaseAndHttpException =
        DatabaseAndHttpException(s"http: ${a.m}")
    }
}
```

そして、次のように用いる。

```scala
def left[A](e: A) = Left[A, Unit](e)

def e1 = left(DatabaseException("db error"))

def e2 = left(HttpException("http error")

{
  import DatabaseAndHttpException._
  val e6 = for {
    a <- e1
    b <- e2.as[DatabaseAndHttpException]
  } yield ()
}
```

前回とは違って、`import`でインスタンスを明示的に呼び出す必要がある。

## 型クラス`:->`を用いた`transitive`の定義

次のようにする。

```scala:Tranform.scala
object :~> {
  implicit def self[A]: A :~> A = new (A :~> A) {
    def apply(a: A): A = a
  }

  implicit def superclass[A, B >: A]: A :~> B = new (A :~> B) {
    def apply(a: A): B = a
  }

  implicit def transitive[A, B, C](implicit F: A :-> B, G: B :~> C): A :~> C = new (A :~> C) {
    def apply(a: A): C = G(F(a))
  }
}
```

このように、ワンステップの変換を表わす`A :-> B`と、ワンステップ以上の変換を表す`B :~> C`を用いて`A :~> C`を作成している。

# 遷移の例

定義した`transitive`を用いて、次のような例を考える。先ほど定義した`DatabaseAndHttpException`と`ReadException`をまとめた`DatabaseAndHttpAndFileReadException`を次のように作成する。

```scala:Exceptions.scala
case class DatabaseAndHttpAndFileReadException(m: String) extends RootException
```

この時点で、継承による階層構造は次のようになっている。

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
|
+---- DatabaseAndHttpAndFileReadException
```

そして、階層構造を表すインスタンスを作成する。

```scala
object DatabaseAndHttpAndFileReadException {
  implicit val databaseAndHttpException = new (DatabaseAndHttpException :-> DatabaseAndHttpAndFileReadException) {
    def apply(a: DatabaseAndHttpException): DatabaseAndHttpAndFileReadException =
      DatabaseAndHttpAndFileReadException(s"database and http: ${a.m}")
  }

  implicit val fileReadException = new (ReadException :-> DatabaseAndHttpAndFileReadException) {
    def apply(a: ReadException): DatabaseAndHttpAndFileReadException =
      DatabaseAndHttpAndFileReadException(s"file read: ${a.m}")
  }
}
```

そして、次のような`for`式を実行する。

```scala
def left[A](e: A) = Left[A, Unit](e)

def e1 = left(DatabaseException("db error"))

def e2 = left(HttpException("http error")

def e3 = left(ReadException("file read error"))

{
  import DatabaseAndHttpException._
  import DatabaseAndHttpAndFileReadException._
  val e9 = for {
    a <- e1
    b <- e2
    c <- e3.as[DatabaseAndHttpAndFileReadException]
  } yield ()
}
```

さらに、`DatabaseAndHttpAndFileReadException`に`WriteException`をも加えた例外`DatabaseAndHttpAndFileException`を作成する。

```scala
case class DatabaseAndHttpAndFileException(m: String) extends RootException
```

まずは同様にインスタンスを定義する。

```scala:Exception.scala
object DatabaseAndHttpAndFileException {
  implicit val databaseAndHttpAndFileReadExcepion = new (DatabaseAndHttpAndFileReadException :-> DatabaseAndHttpAndFileException) {
    def apply(a: DatabaseAndHttpAndFileReadException): DatabaseAndHttpAndFileException =
      DatabaseAndHttpAndFileException(s"database and http and file read: ${a.m}")
  }

  implicit val fileWriteException = new (WriteException :-> DatabaseAndHttpAndFileException) {
    def apply(a: WriteException): DatabaseAndHttpAndFileException =
      DatabaseAndHttpAndFileException(s"file write: ${a.m}")
  }
}
```

そして、次のように実行する。

```scala
def left[A](e: A) = Left[A, Unit](e)

def e1 = left(DatabaseException("db error"))

def e2 = left(HttpException("http error")

def e3 = left(ReadException("file read error"))

def e4 = left(WriteException("file write error"))

{
  import DatabaseAndHttpException._
  import DatabaseAndHttpAndFileReadException._
  import DatabaseAndHttpAndFileException._
  val e10 = for {
    a <- e1
    b <- e2
    c <- e3
    d <- e4.as[DatabaseAndHttpAndFileException]
  } yield ()
}
```

このように、`transitive`はどれだけでもインスタンスを繋げることができる。

# まとめ

このように、前回の記事では定義されていなかった`transitive`を定義して、ExtensibleExceptionをより使いやすくすることができた。
今回の例では、型クラス`:->`のインスタンスを例外を表すクラスのコンパニオンオブジェクトに定義しているため、例外の階層を拡張するたびに`import`が増えているように見えるが、これはどこかにimplicitパラメータの置き場オブジェクトを定義しておいて、全てのimplicitパラメータをひとつの場所に置けば解決できると考えている。
また、このExtensible Exceptionは型クラスによって構成されているため、型クラスを持つ他の言語（たとえばRustなど）への応用もできると考えている。

# 参考文献

- [How to establish an ordering between types in Haskell](http://stackoverflow.com/questions/24775080/how-to-establish-an-ordering-between-types-in-haskell)
