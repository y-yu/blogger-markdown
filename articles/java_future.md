# はじめに

ScalaでJavaのライブラリを利用することがしばしばあるが、ScalaのFutureとJavaのFutureは別である。Scalaを利用する時はJavaのFutureではなく、ScalaのFutureを利用したい。この記事ではJavaのFutureをScalaのFutureへ変換する方法について述べる。なお、この記事の完全なコードは次のGitHubリポジトリに置かれている。

- https://github.com/y-yu/java-future-converter

# 表記

この記事ではScalaの`Future`とJavaの`Future`を次のように区別する。

```scala
import java.util.concurrent.{Future => JavaFuture}
import scala.concurrent.{Future => ScalaFuture}
```

つまり、`JavaFuture[A]`はJavaのFutureであり、一方で`ScalaFuture[A]`はScalaのFutureである。

# 直感的な実装

Stackoverflowなどでは次のようなコードで変換できると書かれている。

```scala:BrokenJavaFutureConverter.scala
object BrokenJavaFutureConverter {
  def toScala[A](jf: JavaFuture[A])(implicit ec: ExecutionContext): ScalaFuture[A] = {
    val p: Promise[A] = Promise[A]

    ec.execute(
      new Runnable {
        override def run() =
          p.complete(
            Try(jf.get())
          )
      }
    )

    p.future
  }

  implicit class RichJavaFuture[A](val jf: JavaFuture[A]) extends AnyVal {
    def asScala(implicit ec: ExecutionContext): ScalaFuture[A] = toScala(jf)
  }
}
```

これはJavaの`Future`をExecutionContextに基づいて実行しScalaの`Promise`で受け取ってそれでScalaの`Future`を返すというコードである。これで一見良さそうで、次のように正常に動作するように見える。

```scala:BrokenJavaFutureConverterSpec.scala
class BrokenJavaFutureConverterSpec extends WordSpec {
  import BrokenJavaFutureConverter._

  trait SetupWithFixedThreadPool {
    val timeout = Duration(1, TimeUnit.SECONDS)

    val threadPool: ExecutorService = Executors.newFixedThreadPool(1)

    val executor: Executor = new ExecutorFromExecutorService(threadPool)

    implicit val ec: ExecutionContextExecutor = ExecutionContext.fromExecutor(executor)
  }

  "toScala" should {
    "return the value" in new SetupWithFixedThreadPool {
      val javaFuture: JavaFuture[Int] = threadPool.submit { () =>
        Thread.sleep(200)
        10
      }

      assert(Await.result(toScala(javaFuture), timeout) == 10)
    }
  }
}
```

一方で次のように、作成したScalaのFutureを`recover`しようとすると正しく動作しない。

```scala:BrokenJavaFutureConverterSpec.scala
"not be able to recover the exception" in new SetupWithFixedThreadPool {
  val javaFuture: JavaFuture[Int] = threadPool.submit{ () =>
    throw new TestException()
  }
 
  val recover = javaFuture.asScala.recover {
    case e: TestException => 10
  }
 
  assertThrows[ExecutionException](Await.result(recover, timeout))
}
```

```scala:TestException.scala
class TestException(message: String = null, cause: Throwable = null)
  extends Exception(message, cause)
```

上記のテストではJavaのFutureは実行時に例外`TestException`を送出し、それを`ScalaFuture#recover`で変換しているはずだが、これの結果を`Await#result`で取り出すと例外`ExecutionException`が送出される。このように、JavaのFutureは実行時の例外を`ExecutionException`でラップしてしまう。これではScalaのFutureとして`recover`がやりずらいので改善を考える。

# `ExecutionException`をアンラップする

次のようなコードで先ほどの問題を解決する。

```scala:JavaFutureConverter.scala
object JavaFutureConverter {
  def toScala[A](jf: JavaFuture[A])(implicit ec: ExecutionContext): ScalaFuture[A] = {
    val p: Promise[A] = Promise[A]

    ec.execute { () =>
      p.complete(
        Try(jf.get()) match {
          case Failure(e: ExecutionException) =>
            Failure(e.getCause)
          case x =>
            x
        }
      )
    }

    p.future
  }

  implicit class RichJavaFuture[A](val jf: JavaFuture[A]) extends AnyVal {
    def asScala(implicit ec: ExecutionContext): ScalaFuture[A] = toScala(jf)
  }
}
```

これはJavaのFutureを`get`したものを`Try`で包み、もし結果が`Failure`でかつ例外の型が`ExecutionException`である場合は、`getCause`を利用してアンラップするようにしている。こうすることで次のように`recover`が動作する。

```scala:JavaFutureConverterSpec.scala
"be able to recover the exception" in new SetupWithFixedThreadPool {
  val javaFuture: JavaFuture[Int] = threadPool.submit { () =>
    throw new TestException()
  }
 
  val recover = javaFuture.asScala.recover {
    case e: TestException => 10
  }
 
  assert(Await.result(recover, timeout) == 10)
}
```

# `ForkJoinPool`による問題

これでよいものができたかに見えたが、調べたところ`ForkJoinPool.commonPool()`といった方法で作成された`ExecutorService`を利用するとこれは次のように正しく動作しないことがあると分った。

```scala:JavaFutureConverterSpec.scala
trait SetupWithForkJoinPool {
  val timeout = Duration(1, TimeUnit.SECONDS)
 
  val forkJoinPool: ExecutorService = ForkJoinPool.commonPool()
 
  val executor: Executor = new ExecutorFromExecutorService(forkJoinPool)
 
  implicit val ec: ExecutionContextExecutor = ExecutionContext.fromExecutor(executor)
}

"return RuntimeException despite it returns IOException if you use the ForkJoinPool executor" in new SetupWithForkJoinPool {
  val javaFuture: JavaFuture[Unit] = forkJoinPool.submit { () =>
    throw new IOException()
  }
 
  assertThrows[RuntimeException](Await.result(javaFuture.asScala, timeout))
}
```

これは`IOException`を送出しているにも関わらず、`RuntimeException`にラップされていることを示している。このように、この`JavaFutureConverter#toScala`は利用する`ExecutorService`によっては正しく動作しないことがあることに注意が必要である。もしこのコードを本番で利用する場合は、そのコードがどのような方法で作成した`ExecutorService`を利用しているのかを調べて、その`ExecutorService`を利用したテストを実行してからこのコードを利用するべきである。

# がくぞさんからのアドバイス

がくぞさんから次のようなコードでもよいという意見をいただいた。

<blockquote class="twitter-tweet" data-lang="ja"><p lang="ja" dir="ltr">Future(jf.get()).transform {<br>  case Failure(e: ExecutionException) =&gt; Failure(e.getCause)<br>  case x =&gt; x<br>}<br>で同じになるかもです</p>&mdash; がくぞ (@gakuzzzz) <a href="https://twitter.com/gakuzzzz/status/872580192996216832">2017年6月7日</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

`JavaFutureConverter#toScala`は`ExecutionContext`を暗黙に受け取ってそれでJavaのFutureを実行するが、ScalaのFutureも同じような動作だったのでこちらの方がシンプルであるという理由でこちらに修正した。

```scala:JavaFutureConverter.scala
object JavaFutureConverter {
  def toScala[A](jf: JavaFuture[A])(implicit ec: ExecutionContext): ScalaFuture[A] = {
    ScalaFuture(jf.get()).transform {
      case Failure(e: ExecutionException) =>
        Failure(e.getCause)
      case x => x
    }
  }
}
```

# まとめ

JavaのFutureをScalaのFutureへ変換するのは思っていたよりも難しいということが分かった。もしこれよりもよい方法があれば、気軽にこの記事のコメントなどで指摘して欲しい。
