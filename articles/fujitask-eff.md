---
title: Extensible Effectsでトランザクションモナド“Fujitask”を作る
tags: Scala FunctionalProgramming 関数型プログラミング extensible-effects モナド
author: yyu
slide: false
---
# はじめに

ScalaやHaskellなどでは**モナド**を利用して副作用[^side_effect]を抽象化するということがしばしば行われる。**Fujitask**はScalaで実装された1つのモナドで、データベースへのアクセスに関するトランザクション制御を抽象化した。ところがモナドは`Reader[Future[Either[Error, Option[A]]]]`のようにいくつものモナドが入れ子になってしまったとき、Scalaの`for`式のようなモナド構文では内側のモナドへのアクセスが難しくなってしまう。
この問題へのアプローチとして有名なものに**モナドトランスフォーマー**がある。あるモナドトランスフォーマー`T`は任意モナド`M`を引数に取って`T[M]`となる新しい1つのモナドとなり、このモナド`T[M]`は`T`と`M`の両方のモナドの能力を持つ。たとえばエラーと成功を表すようなモナドトランスフォーマー`EitherT`と、非同期実行を表すモナド`Future`を合成した`EitherT[Future]`は`Future[Either]`のような能力となり、これは`Either`と`Future`の機能を同時に使えるようなモナドとなる。ただしモナドトランスフォーマーは`Either`に対して`EitherT`や`Reader`に対して`ReaderT`など次々と生みだしていく必要がある。
**Extensible Effects**とはモナドトランスフォーマーをよりよく改良したものであり、モナドトランスフォーマーのような新しい構造を必要とせずに異なるモナドを合成できる。ScalaではExtensible Effectsの実装として[atnos-eff](https://github.com/atnos-org/eff)や[kits-eff](https://github.com/halcat0x15a/kits-eff)があり、今回はkits-effを利用してExtensible EffectsによるFujitaskを実装した。
この記事ではまずFujitaskについて簡単な解説を行い、そして今回のExtensible Effects版Fujitaskの利用例を見せる。そして具体的な実装を紹介し、最後にまとめと参考文献の紹介を行う。

この記事について間違った点などがあれば気軽にコメントなどで教えてほしい。なお完全なソースコードは下記のリポジトリに置かれている。

- https://github.com/y-yu/fujitask-eff

[^side_effect]: 最近は「副作用」という言葉ではなくて「計算効果（Computational effect）」という言葉で表現されることもある。

# Fujitaskとは？

Fujitaskはデータベースなどのトランザクションを管理するモナドであり、次のような特徴を持つ。

- トランザクションが読み込みなのか、読み込みと書き込みの両方ができるのかを**型レベルの計算**により決定する

たとえばFujitaskでは読み込みしかできないReadトランザクションと、読み込みと書き込みができるReadWriteトランザクションを合成すると、型レベルの計算によりReadWriteのトランザクションとなる。実現の詳しい解説は割愛するが、これはサブタイプにより実現されている。それゆえにHaskell由来のExtensible Effectsへ持ち込めるのかは興味深い話題であり、かつて色々と考えたもののうまくいかなかった。
kits-effではモナドスタック[^monad_stack]を型の積として表すため、こちらであればサブタイプを利用したFujitaskを作成できると考えた。atnos-effが用いるような型レベルのリスト的な構造ではFujitaskのように2つ型の共通のサブタイプを見つけてそれに置き換えるといったことが難しい。一方でkits-effでは`with`を利用した型の積を利用しているので、うまく工夫することでサブタイプを利用することができるのではないかと考えた。

[^monad_stack]: 複数種類のモナドをリストとして表現したものであり、たとえば`Reader[Future[Either[Error, Option[A]]]]`であれば`Stack(Reader, Future, Either, Option)`というようなイメージである。

# 利用例

解説のまえに、まずはどのように利用できるのかを見てみる。普通のモナドと同じように`for-yield`式の中で利用できる。

```scala
case class User(id: Long, name: String)
// create table `user` (
//   `id` bigint not null auto_increment,
//   `name` varchar(64) not null
// )

val logger: Logger = LoggerFactory.getLogger(Main.getClass)

val eff1 = for {
  user1 <- userRepository.read(1L)
  _     <- userRepository.create("test")
  user2 <- userRepository.read(1L)
} yield {
  logger.info(s"user1 is $user1")
  logger.info(s"user2 is $user2")
}
Fujitask.run(eff1)
```

この結果は次のようになる。

```
02:08:31.610 [run-main-1] INFO  repository.impl.jdbc.package$ - ReadWriteRunner begin --------->
02:08:31.672 [scala-execution-context-global-82] INFO  Main$ - user1 is None
02:08:31.672 [scala-execution-context-global-82] INFO  Main$ - user2 is Some(User(1,test))
02:08:31.674 [scala-execution-context-global-82] INFO  repository.impl.jdbc.package$ - <--------- ReadWriteRunner end
```

`id = 1`となるユーザーが存在しないため最初は`None`となり、その後`userRepository.create`でユーザーを作ったことで`user2`では`Some`となっている。ここでは読み込み（`read`）と書き込み（`create`）を行っているためログとして`ReadWriteRunner begin`/`ReadWriteRunner end`が出力されている。
この後たとえば次のように読み込みだけを行ってみる。

```scala
val eff2 = for {
  user3 <- userRepository.read(1L)
} yield {
  logger.info(s"user3 is $user3")
}
Fujitask.run(eff2)
```

```
02:08:31.675 [scala-execution-context-global-84] INFO  repository.impl.jdbc.package$ - ReadRunner begin --------->
02:08:31.676 [scala-execution-context-global-104] INFO  Main$ - user3 is Some(User(1,test))
02:08:31.677 [scala-execution-context-global-104] INFO  repository.impl.jdbc.package$ - <--------- ReadRunner end
```

さきほど作ったユーザーが表示された。ここでは読み込みしか行っていないので`ReadRunner begin`/`ReadRunner end`がログに出力されている。

これだけではモナド版Fujitaskと変わりないが、Extensible Effects版はモナドトランスフォーマーを定義することなくたとえば`Reader`モナドと組み合わせて次のように使うことができる。

```scala
val eff3 = for {
  name <- Reader.ask[String]
  user <- userRepository.create(name)
  user4 <- userRepository.read(user.id)
} yield {
  logger.info(s"user4 is $user4")
}
Fujitask.run(Reader.run("piyo")(eff3))
```

```
02:20:15.892 [scala-execution-context-global-134] INFO  repository.impl.jdbc.package$ - ReadWriteRunner begin --------->
02:20:15.893 [scala-execution-context-global-134] INFO  Main$ - user4 is Some(User(2,piyo))
02:20:15.893 [scala-execution-context-global-133] INFO  repository.impl.jdbc.package$ - <--------- ReadWriteRunner end
```

`Reader.run`の引数`piyo`を`name`に持つユーザーが作成され、それが表示されている。かつ読み込み・書き込みの両方なので`ReadWriteRunner`が利用されている。
このFujitaskは、`Reader`以外にもkits-effで定義されている任意のモナドと組み合わせることができる。

# 実装

ここでは詳しい実装について解説する。ただ[モナド版Fujitaskの記事](https://qiita.com/pab_tech/items/86e4c31d052c678f6fa6)と比較すると、ほとんどが同じように作られていることが分かると思う。

## エフェクトの定義

まずはFujitaskを表すエフェクト[^effect]`Fujitask`を定義する。

```scala:Fujitask.scala
sealed abstract class Fujitask extends Product with Serializable

object Fujitask {
  final case class Execute[A](f: ExecutionContext => Future[A])
    extends Fujitask with Fx[A]
  
  abstract case class Transaction() extends Fujitask with Fx[Transaction]
  
  final case class Ask[I <: Transaction]() extends Fujitask with Fx[I]
}
```

[^effect]: **エフェクト**とは副作用（計算効果）を抽象化したものである。モナドは副作用を抽象化する方法の1つであることから、ここではモナドのようなものと思えばよい。Extensible Effectsは（1）エフェクトをスタックに詰み、計算の合成を行うが、この時点ではまだスレッドを起動したりデータベースへ接続したりといった具体的な副作用は生じさせない。そして次に（2）インタープリターによってエフェクトが入ったスタックを解析し、それに基づいた副作用を生じさせる。
3つのデータ構造は次のような意味を持っている。

<dl>
  <dt><code>Execute</code></dt>
  <dd><code>ExecutionContext</code>を利用して最終的な計算を行う。</dd>

  <dt><code>Ask</code></dt>
  <dd>Readerモナドの<code>ask</code>に相当し、トランザクション内のデータベースセッションを取得する。</dd>

  <dt><code>Session</code></dt>
  <dd>具体的なトランザクション用の情報のための抽象的なデータ構造を表す。</dd>
</dl>

`Ask`があるのはモナド版のFujitaskと変わらず、`Execute`はモナド版の`Task.apply`に相当する。
またこれらをインスタンシエイトするための関数を次のように作っておく。

```scala:Fujitask.scala
object Fujitask {
  def apply[I, A](a: => A): Eff[I, A] =
    Eff(Execute(Future(a)(_)))

  def ask[R <: Transaction, I <: R]: Eff[R, I] =
    Eff(Ask())
}
```

## トランザクションの定義

次にモナド版Fujitaskと同様に抽象的なトランザクションと具体的なトランザクションを定義する。トランザクションの管理に必要なデータベースとのセッションなどはデータベースの種類やデータベース用のライブラリーに依存する。そこで抽象的な部分でReadトランザクションやReadWriteトランザクションなどと定義しておいて、具体的なものとしてたとえば[ScalikeJDBC](http://scalikejdbc.org/)の実装を利用するものを定義することで、インターフェースと実装を分離しやすくなる。
まずは抽象的なトランザクションの定義である。

```scala:Transaction.scala
trait ReadTransaction extends Transaction

trait ReadWriteTransaction extends ReadTransaction
```

`Transaction`はさきほど作成した`Fujitask.Transaction`である。`Transaction`が別の場所にあること除いて、モナド版Fujitaskと全く同じである。
次に今回は例としてScalikeJDBCを利用する。

```scala:ScalikeJDBCTransaction.scala
trait ScalikeJDBCTransaction extends Transaction {
  val ctx: DBSession
}

class ScalikeJDBCReadTransaction(val ctx: DBSession)
    extends ScalikeJDBCTransaction
      with ReadTransaction

class ScalikeJDBCWriteTransaction(override val ctx: DBSession)
  extends ScalikeJDBCReadTransaction(ctx)
    with ReadWriteTransaction
```

これについてもモナド版とほとんど同じである。

## リポジトリ層の定義

次に実際にデータベースへアクセスする部分のインターフェースと実装を作っていく。いま次のようなテーブル`user`によってユーザーのデータを表す`User`がある

```sql
create table `user` (
  `id` bigint not null auto_increment,
  `name` varchar(64) not null
)
```

```scala:User.scala
case class User(id: Long, name: String)
```

これへの操作のインターフェースを次のように定義する。

```scala:UserRepository.scala
trait UserRepository {
  def create(name: String): Eff[ReadWriteTransaction, User]

  def read(id: Long): Eff[ReadTransaction, Option[User]]

  def update(user: User): Eff[ReadWriteTransaction, Unit]

  def delete(id: Long): Eff[ReadWriteTransaction, Unit]
}
```

ここではインターフェースなので抽象的なトランザクションを表す`ReadTransaction`や`ReadWriteTransaction`を利用している。そして具体的な実装は次のようになる。

```scala:UserRepositoryImpl.scala

class UserRepositoryImpl extends UserRepository {
  def create(name: String): Eff[ReadWriteTransaction, User] =
    Fujitask.ask map { (i: ScalikeJDBCWriteTransaction) =>
      implicit val session: DBSession = i.ctx

      val sql = sql"""insert into user (name) values ($name)"""
      val id = sql.updateAndReturnGeneratedKey.apply()
      User(id, name)
    }

  def read(id: Long): Eff[ReadTransaction, Option[User]] =
    Fujitask.ask map { (i: ScalikeJDBCReadTransaction) =>
      implicit val session: DBSession = i.ctx

      val sql = sql"""select * from user where id = $id"""
      sql.map(rs => User(rs.long("id"), rs.string("name"))).single.apply()
    }

  def update(user: User): Eff[ReadWriteTransaction, Unit] =
    Fujitask.ask map { (i: ScalikeJDBCWriteTransaction) =>
      implicit val session: DBSession = i.ctx

      val sql = sql"""update user set name = ${user.name} where id = ${user.id}"""
      sql.update.apply()
    }

  def delete(id: Long): Eff[ReadWriteTransaction, Unit] =
    Fujitask.ask map { (i: ScalikeJDBCWriteTransaction) =>
      implicit val session: DBSession = i.ctx

      val sql = sql"""delete user where id = $id"""
      sql.update.apply()
    }
}
```

`Fujitask.ask`によってScalikeJDBCのセッションを取得し、それを用いて具体的なSQLを発行する。

## `FujitaskRunner`の定義

`FujitaskRunner`という型クラスを次のように定義する。

```scala:FujitaskRunner.scala
trait FujitaskRunner[I] {
  def apply[A](task: I => Future[A]): Future[A]
}
```

これは型パラメーター`I`を引数にとり`Future[A]`となるような関数`task`を受けとり、その結果をとして`Future[A]`を返す。ScalikeJDBCによる実装は次のようになる。

```scala:package.scala
package object jdbc {
  lazy val logger: Logger = LoggerFactory.getLogger(this.getClass)

  implicit def readRunner[I >: ReadTransaction](implicit ec: ExecutionContext): FujitaskRunner[I] =
    new FujitaskRunner[I] {
      def apply[A](task: I => Future[A]): Future[A] = {
        logger.info("ReadRunner begin --------->")
        val session = DB.readOnlySession()
        val future = task(new ScalikeJDBCReadTransaction(session))
        future.onComplete { _ =>
          logger.info("<--------- ReadRunner end")
          session.close()
        }
        future
      }
    }

  implicit def readWriteRunner[I >: ReadWriteTransaction](implicit ec: ExecutionContext): FujitaskRunner[I] =
    new FujitaskRunner[I] {
      def apply[A](task: I => Future[A]): Future[A] = {
        logger.info("ReadWriteRunner begin --------->")
        val future = DB.futureLocalTx(session => task(new ScalikeJDBCWriteTransaction(session)))
        future.onComplete(_ =>
          logger.info("<--------- ReadWriteRunner end")
        )
        future
      }
    }
}
```

このように型パラメーターの下限を利用することでReadトランザクション時には`DB.readOnlySession()`で読み込み専用のセッションを取得し、そして一方でReadWriteトランザクションのときは`DB.futureLocalTx`でトランザクションを発生させる。
型パラメーター`I`は、後述するインタープリターの実行するコードの呼び出し部分でScalaのコンパイラーがコンパイル時に適切に計算する。

## インタープリターの定義

インタープリターは実際にエフェクトスタックに積まれたエフェクトを解析して、副作用を生じさせる。たとえば`Future`を表すようなエフェクトがあるなら、実際にスレッドを起動するとか、あるいはファイルへのIOを行うエフェクトがあるならば`scala.io.Source`などを利用してファイルへアクセスするなどである。今考えている`Fujitask`はデータベースのトランザクションなので、ここでデータベースへトランザクションを発行するといったことが行われる。
これが最も複雑ではあると思うが、次のようになっている。

```scala:Fujitask.scala
object Fujitask {
  def run[I <: Transaction: Manifest, A](
    eff: Eff[I, A]
  )(
    implicit runner: FujitaskRunner[I],
    ec: ExecutionContext
  ): Future[A] = {
    def handle(i: I) = new ApplicativeInterpreter[Fujitask, Any] {
      override type Result[T] = Future[T]

      def pure[T](a: T): Eff[Any, Result[T]] = Eff.Pure(Future.successful(a))

      def flatMap[T, B](fa: Fujitask with Fx[T])(k: T => Eff[Any, Future[B]]): Eff[Any, Future[B]] =
        fa match {
          case Execute(f) =>
            Eff.Pure(f(ec).flatMap(a => Eff.run(k(a))))
          case _: Ask[I] =>
            k(i.asInstanceOf[T])
        }

      def ap[T, B](fa: Fujitask with Fx[T])(k: Eff[Any, Result[T => B]]): Eff[Any, Result[B]] =
        fa match {
          case Execute(f) =>
            Eff.Pure(f(ec).flatMap(a => Eff.run(k).map(_(a))))
          case _: Ask[I] =>
            k.map(_.map(_(i.asInstanceOf[T])))
        }

      def map[T, B](fa: Future[T])(k: T => B): Future[B] = fa.map(k)
    }

    runner(i => Eff.run(handle(i)(eff.asInstanceOf[Eff[Fujitask, A]])))
  }
}
```

まず最下部ではさきほどの`TaskRunner`を利用している。`i`には`ScalikeJDBCReadTransaction`などの具体的なトランザクションが入ることになる。
適切な`TaskRunner`が呼びだされることを説明するため、型`Eff[R, A]`について述べる。`R`はエフェクトスタック[^effect_stack]を表し、`A`はトランザクション内で実行された計算の結果を表す。上記の関数`run`は型パラメーター`I <: Transaction: Manifest`と`A`を取り、引数に`eff: Eff[I, A]`を取っている。`Manifest`については本質的ではないので説明しないが、この型`I`は型`Transaction`のサブタイプであるので、エフェクトスタックそのものが`Transaction`のサブタイプでなければならない。
この型パラメーター`I`が、たとえば`ReadTransaction`と`ReadWriteTransaction`を`flatMap`したならば`ReadWriteTransaction`になる必要がある。いま`Eff[R, A]`の`flatMap`は次のように実装されている。

[^effect_stack]: エフェクト（たとえば`Fujitask`など）をモナドスタックのように並べたものである。モナドスタックと似ているが一応この記事ではモナドはエフェクトの具体的な実装であると区別しているため、呼び分けることとした。

```scala:Eff.scala
def flatMap[S, B](f: A => Eff[S, B]): Eff[R with S, B] =
  this match {
    case Eff.Pure(v) =>
      f(v)
    case Eff.Impure(u, k) =>
      Eff.Impure(u.extend[S], k :+ f)
  }
```

エフェクトスタック`R`と別のエフェクトスタック`S`を合成して`R with S`としている。より具体的に、次のような例を考えてみる。

- `Eff[ReadTransaction, A]`と`Eff[ReadTransaction, B]`を合成した場合、`Eff[ReadTransaction with ReadTransaction, B]`となる。このとき

    ```math
\def\RT{\color{blue}{\text{ReadTransaction}}\;}
\def\RWT{\color{red}{\text{ReadWriteTransaction}}\;}
\def\with{\text{with}\;}
\RT =\, \RT \with \RT
    ```
  となり[^type_equal]ここでは`runner`として`readRunner`が選択される

- 同様にいくつかの合成の結果`Eff[ReadTransaction with ReadWriteTransaction with ReadTransaction with ReadTransaction, A]`となった場合

    ```math
\RWT <:\, \RT
    ```
  なので、

    ```math
\RWT =\, \RT \with \RWT \with \RT \with \RT

    ```
  となり、`runner`として`readWriteRunner`が選択される

[^type_equal]: それほど重要ではないが、型$A, B$が等しい（$A = B$）とは$A$は$B$のサブタイプかつ$B$は$A$のサブタイプである（$A = B \Leftrightarrow (A <: B \land B <: A)$ことを指す。また$A <: B$とは型$A$は型$B$のサブタイプであることを表す

このようにしてサブタイプによる型の交わりと型クラスを利用することで巧妙に適した`FujitaskRunner`のインスタンスを選択している。

さて、次にインタープリターの内部について説明する。`ApplicativeInterpreter`をインスタンシエイトしており、この中で説明するべきところは`flatMap`メソッドである。

```scala
def flatMap[T, B](fa: Fujitask with Fx[T])(k: T => Eff[Any, Future[B]]): Eff[Any, Future[B]] =
  fa match {
    case Execute(f) =>
      Eff.Pure(f(ec).flatMap(a => Eff.run(k(a))))
    case _: Ask[I] =>
      k(i.asInstanceOf[T])
  }
```

`fa`とはエフェクトであり、この型`Fujitask with Fx[T]`は値`fa`についての特徴を次のように説明している。

- `Fujitask`のエフェクトである（`Fujitask`）
- 継続（残りの計算）`k`を開始するために必要な値の型が`T`である（`Fx[T]`）

そして`fa`に基づいて継続`k`を処理することができる。`fa`を`Execute`のケースと`Ask`のケースで場合わけをして、次のように処理を行っている。

### `Execute(f)`の場合

関数`f: ExecutionContext => Future[A]`を`run`が呼び出されたときに渡された`ExecutionContext`を利用して起動する。すると当然`Future[A]`となる値が得られる。さて、`Execute`の定義はこのようであった。

```scala
final case class Execute[A](f: ExecutionContext => Future[A])
  extends Fujitask with Fx[A]
```

`Fx[A]`を継承しているので、`k: A => Eff[Any, Future[B]]`となる。いま`Future[A]`が`f(ec)`で得られたため、これを`flatMap`することで`A`の値（`a`）を得られる。あとは`k(a)`で継続を起動すればよい。`k`の返り値は`Eff[Any, Future[B]]`であるが、`Eff.run`によって「もし`k(a)`の返り値のエフェクトスタックが空になっているならば、結果の型`Future[B]`の値を取り出す」ということができる[^if_not_empty]。これにより処理が終了する。

[^if_not_empty]: もしエフェクトスタックが空ではない値`eff: Eff[R, A]`によって`Eff.run(eff)`を実行した場合、ランタイムエラーを送出する。

### `Ask`の場合

`Ask`は次のようであった。

```scala
final case class Ask[I <: Transaction]() extends Fujitask with Fx[I]
```

`Fx[I]`なので継続`k`を呼びだすための引数の型`T`は`I`であるということになる。したがって継続`k`に`FujitaskRunner`から渡された`i`を渡して起動するだけでよい[^as_instance_of]。

[^as_instance_of]: パターンマッチの結果`Ask`となった時点で`T = I`という型を決定できそうだが、Scalaの現時点でのコンパイラーはそれを検出してくれない。そのためコンパイルを通すためここでは`k(i.asInstanceOf[T])`としている。

# まとめ

このようにしてExtensible Effects版のFujitaskを実装することができた。しかしこの実装は次のような問題があるのではないか？という指摘もある。

- `Transaction`はエフェクトを表現するが、これが`sealed`されていないのでユーザーが任意のエフェクトを作ってしまう可能性がある

エフェクトを任意に作ることができてしまうので、このエフェクトのインタープリター（Fujitaskで言えば`Fujitask.run`）が意図しないようなエフェクトをエフェクトスタックに詰めこめてしまう。するとそのエフェクトはインタープリターによって処理されず、`Eff.run`がランタイムエラーを生じさせる可能性がある。
まだよく考えたわけではないものの、もし`Transaction`を継承したよく分からないエフェクトがあったとしても、適切な`FujitaskRunner[I]`が見つからずにコンパイルエラーとなるような予感もある。これについてはもう少し考えてみて、インタープリターが処理できないかつランタイムエラーとなるような状態が発生するかを検証しようと思う。

# 謝辞

Extensible Effects版Fujitaskを作るにあたって、[@halcat0x15a](https://twitter.com/halcat0x15a)さんにはとても有用なコメントやコードの修正など様々な協力をしていただいた。

# 参考文献

- [進捗大陸05](https://booth.pm/ja/items/1309694)（“ScalaらしいEffを目指して”）
    - 実装に利用したkits-effの実装詳細に関して作者の@halcat0x15aさんにより解説されている記事
- [ドワンゴ秘伝のトランザクションモナドを解説！](https://qiita.com/pab_tech/items/86e4c31d052c678f6fa6)
- [筆者が社内勉強会でFujitask（モナド版）の説明のために作成したスライド](https://y-yu.github.io/fujitask-slide/fujitask_without_animation.pdf)
- [kits-eff](https://github.com/halcat0x15a/kits-eff)
- [Freer Monads, More Extensible Effects](http://okmij.org/ftp/Haskell/extensible/more.pdf)


